"""Судейство открытых ответов — всегда в фоне.

Сдача попытки не делает исходящих вызовов вообще: она кладёт ответ в очередь
и возвращает разбор по вопросам с вариантами. Судья работает отдельно, и
отсутствие вердикта — штатное состояние, а не ошибка. Иначе сбой у провайдера
в момент, когда тридцать шесть человек жмут «Сдать», останавливал бы лекцию.

Вызов модели идёт по конвенции репозитория: OpenAI-совместимый chat/completions,
модель из REVIEW_MODEL, ключ из REVIEW_API_KEY / DEEPSEEK_API_KEY.
"""

from __future__ import annotations

import asyncio
import json
import logging

import httpx

from .bank import Bank
from .config import Settings
from .store import Store

log = logging.getLogger("quizapp.judge")

SYSTEM = (
    "Ты проверяешь короткий письменный ответ студента на вопрос по лекции. "
    "Засчитывай ответ по смыслу, а не по совпадению слов: формулировка своими "
    "словами, другой порядок и опечатки — не повод не засчитать. Не засчитывай, "
    "если ключевая мысль отсутствует, искажена или ответ пустой. "
    "Отвечай строго объектом JSON с полями correct (true/false) и rationale "
    "(одно предложение по-русски, обращённое к студенту)."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "correct": {"type": "boolean"},
        "rationale": {"type": "string"},
    },
    "required": ["correct", "rationale"],
    "additionalProperties": False,
}


def build_prompt(*, question: str, reference: str, credit_if: str, answer: str) -> str:
    parts = [f"Вопрос:\n{question}", f"Эталонный ответ:\n{reference}"]
    if credit_if:
        parts.append(f"Засчитывать, если:\n{credit_if}")
    parts.append(f"Ответ студента:\n{answer if answer.strip() else '(пусто)'}")
    return "\n\n".join(parts)


def parse_verdict(raw: str) -> tuple[bool, str]:
    """Разобрать ответ модели. Кидает ValueError, если это не наш JSON."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"в ответе модели нет объекта JSON: {raw[:200]}")
    data = json.loads(text[start : end + 1])
    if "correct" not in data:
        raise ValueError(f"в ответе модели нет поля correct: {raw[:200]}")
    return bool(data["correct"]), str(data.get("rationale", "")).strip()


class Judge:
    def __init__(self, settings: Settings, store: Store, banks: dict[str, Bank]) -> None:
        self.s = settings
        self.store = store
        self.banks = banks
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    # --- вызов модели -----------------------------------------------------

    async def ask(self, prompt: str) -> tuple[bool, str]:
        payload = {
            "model": self.s.llm_model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "verdict", "strict": True, "schema": SCHEMA},
            },
        }
        async with httpx.AsyncClient(timeout=self.s.llm_timeout_sec) as client:
            resp = await client.post(
                f"{self.s.llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.s.llm_api_key}"},
                json=payload,
            )
        if resp.status_code == 400 and "response_format" in resp.text:
            # Провайдер не умеет json_schema — просим тот же JSON словами.
            payload.pop("response_format")
            payload["messages"][0]["content"] += " Ответ — только JSON, без пояснений вокруг."
            async with httpx.AsyncClient(timeout=self.s.llm_timeout_sec) as client:
                resp = await client.post(
                    f"{self.s.llm_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.s.llm_api_key}"},
                    json=payload,
                )
        if resp.status_code != 200:
            raise RuntimeError(f"модель ответила {resp.status_code}: {resp.text[:200]}")
        return parse_verdict(resp.json()["choices"][0]["message"]["content"])

    # --- одна задача из очереди ------------------------------------------

    async def process_one(self) -> bool:
        """Взять и обработать одну задачу. False — очередь пуста."""
        row = await asyncio.to_thread(self.store.claim_judgement)
        if row is None:
            return False

        answer_id = row["answer_id"]
        try:
            answer = await asyncio.to_thread(self._answer_context, answer_id)
        except Exception as exc:  # noqa: BLE001
            await asyncio.to_thread(
                self.store.finish_judgement, answer_id, is_correct=None, error=str(exc)
            )
            return True

        try:
            correct, rationale = await self.ask(build_prompt(**answer))
        except Exception as exc:  # noqa: BLE001
            log.warning("судейство %s не удалось: %s", answer_id, exc)
            await asyncio.to_thread(
                self.store.finish_judgement, answer_id, is_correct=None, error=str(exc)
            )
            return True

        await asyncio.to_thread(
            self.store.finish_judgement, answer_id, is_correct=correct, rationale=rationale
        )
        return True

    def _answer_context(self, answer_id: int) -> dict:
        with self.store._lock:  # noqa: SLF001 - один модуль, одна ответственность
            row = self.store._db.execute(  # noqa: SLF001
                "SELECT a.question_id, a.text, q.lecture FROM answer a"
                " JOIN attempt t ON t.id = a.attempt_id"
                " JOIN quiz q ON q.id = t.quiz_id WHERE a.id = ?",
                (answer_id,),
            ).fetchone()
        if row is None:
            raise RuntimeError(f"ответа {answer_id} нет")
        bank = self.banks.get(row["lecture"])
        if bank is None:
            raise RuntimeError(f"банка лекции {row['lecture']} нет")
        question = bank.by_id.get(row["question_id"])
        if question is None:
            raise RuntimeError(f"вопроса {row['question_id']} нет в банке")
        return {
            "question": question.prompt,
            "reference": question.reference,
            "credit_if": question.credit_if,
            "answer": row["text"] or "",
        }

    # --- фоновый цикл -----------------------------------------------------

    async def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                busy = await self.process_one()
            except Exception:  # noqa: BLE001 - цикл не имеет права умереть
                log.exception("сбой в цикле судейства")
                busy = False
            if not busy:
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=self.s.judge_poll_sec)
                except asyncio.TimeoutError:
                    pass

    def start(self) -> None:
        if not self.s.judge_enabled:
            log.info("судья выключен (QUIZ_JUDGE_ENABLED)")
            return
        if not self.s.judge_configured:
            log.warning("нет REVIEW_API_KEY / DEEPSEEK_API_KEY — открытые ответы останутся без вердикта")
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None
