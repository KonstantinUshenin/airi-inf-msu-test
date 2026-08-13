"""Разбор банка вопросов из markdown.

Формат — markdown с жёсткой разметкой, а не yaml: банк правят люди в pull
request, и он должен читаться как остальные материалы курса (docs/adr/0007).
Плата за это — хрупкий парсер, поэтому здесь всё строгое: любое отклонение
превращается в ошибку с номером строки, а не в молча съеденный вопрос.

Разбор ничего не знает про то, кто его позвал. Линтер (`tools/lint_quiz_banks.py`)
и сервис пользуются одной и той же функцией `parse_bank`, чтобы CI проверял
ровно тот файл, который потом прочитает сервис.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

MC_PREFIX = "q-mc-"
OPEN_PREFIX = "q-open-"

RE_META = re.compile(r"^<!--\s*quiz-bank:\s*lecture=([a-z0-9][a-z0-9-]*)\s*-->\s*$")
RE_HEADING = re.compile(r"^(#{1,3})\s+(.*\S)\s*$")
RE_QUESTION_ID = re.compile(r"^q-(mc|open)-[a-z0-9][a-z0-9-]*$")
RE_OPTION = re.compile(r"^-\s+\[([ xX])\]\s+(.*\S)\s*$")
RE_SLIDE = re.compile(r"^>\s*Слайд:\s*(.*\S)\s*$")

FIELD_REFERENCE = "**Эталон:**"
FIELD_CREDIT = "**Засчитывать, если:**"


class BankError(Exception):
    """Банк непригоден к использованию. Текст уже содержит номера строк."""


@dataclass
class Option:
    text: str
    correct: bool


@dataclass
class Question:
    id: str
    kind: str  # "mc" | "open"
    prompt: str
    line: int
    options: list[Option] = field(default_factory=list)
    reference: str = ""
    credit_if: str = ""
    slide: str = ""

    @property
    def correct_index(self) -> int:
        for i, opt in enumerate(self.options):
            if opt.correct:
                return i
        raise BankError(f"{self.id}: нет верного варианта")


@dataclass
class Bank:
    lecture: str
    title: str
    path: Path | None
    questions: list[Question]

    @property
    def by_id(self) -> dict[str, Question]:
        return {q.id: q for q in self.questions}

    @property
    def mc(self) -> list[Question]:
        return [q for q in self.questions if q.kind == "mc"]

    @property
    def open(self) -> list[Question]:
        return [q for q in self.questions if q.kind == "open"]


def parse_bank(text: str, *, path: Path | None = None) -> tuple[Bank, list[str]]:
    """Разобрать банк. Возвращает (банк, список проблем).

    Список проблем пуст ровно тогда, когда банк корректен. Банк возвращается
    и при проблемах — линтеру нужно показать всё сразу, а не первую ошибку.
    """
    problems: list[str] = []
    lecture = ""
    title = ""
    questions: list[Question] = []
    current: Question | None = None
    # Куда сейчас дописываются продолжения многострочного поля.
    pending: str | None = None

    def finish() -> None:
        nonlocal current, pending
        if current is not None:
            current.prompt = current.prompt.strip()
            current.reference = current.reference.strip()
            current.credit_if = current.credit_if.strip()
            questions.append(current)
        current = None
        pending = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        stripped = line.strip()

        meta = RE_META.match(stripped)
        if meta:
            if lecture:
                problems.append(f"строка {lineno}: повторный заголовок quiz-bank")
            lecture = meta.group(1)
            continue

        heading = RE_HEADING.match(line)
        if heading:
            level, body = len(heading.group(1)), heading.group(2)
            if level == 1:
                if title:
                    problems.append(f"строка {lineno}: второй заголовок первого уровня")
                title = body
                finish()
            elif level == 2:
                finish()  # разделы носят чисто оформительский смысл
            else:
                finish()
                if not RE_QUESTION_ID.match(body):
                    problems.append(
                        f"строка {lineno}: «{body}» не похоже на идентификатор вопроса "
                        f"(ожидается {MC_PREFIX}… или {OPEN_PREFIX}…, только строчные латинские и дефисы)"
                    )
                    continue
                kind = "mc" if body.startswith(MC_PREFIX) else "open"
                current = Question(id=body, kind=kind, prompt="", line=lineno)
                pending = "prompt"
            continue

        if current is None:
            continue  # преамбула банка между заголовками — свободный текст

        option = RE_OPTION.match(stripped)
        if option:
            if current.kind != "mc":
                problems.append(
                    f"строка {lineno}: у открытого вопроса {current.id} есть вариант ответа"
                )
                continue
            current.options.append(
                Option(text=option.group(2), correct=option.group(1).lower() == "x")
            )
            pending = None
            continue

        slide = RE_SLIDE.match(stripped)
        if slide:
            current.slide = slide.group(1)
            pending = None
            continue

        if stripped.startswith(FIELD_REFERENCE):
            if current.kind != "open":
                problems.append(
                    f"строка {lineno}: эталон указан у вопроса с вариантами {current.id}"
                )
                continue
            current.reference += stripped[len(FIELD_REFERENCE) :].strip() + "\n"
            pending = "reference"
            continue

        if stripped.startswith(FIELD_CREDIT):
            if current.kind != "open":
                problems.append(
                    f"строка {lineno}: критерий засчитывания у вопроса с вариантами {current.id}"
                )
                continue
            current.credit_if += stripped[len(FIELD_CREDIT) :].strip() + "\n"
            pending = "credit_if"
            continue

        if not stripped:
            # Пустая строка закрывает многострочное поле, но не сам вопрос:
            # между формулировкой и вариантами она обязана быть.
            if pending in ("reference", "credit_if"):
                pending = None
            continue

        if pending == "prompt":
            current.prompt += stripped + "\n"
        elif pending == "reference":
            current.reference += stripped + "\n"
        elif pending == "credit_if":
            current.credit_if += stripped + "\n"
        else:
            problems.append(
                f"строка {lineno}: текст «{stripped[:40]}» не относится ни к одному полю "
                f"вопроса {current.id}"
            )

    finish()

    if not lecture:
        problems.append("нет строки <!-- quiz-bank: lecture=<слаг> -->")
    if not title:
        problems.append("нет заголовка первого уровня")

    problems.extend(_validate(questions))
    return Bank(lecture=lecture, title=title, path=path, questions=questions), problems


def _validate(questions: list[Question]) -> list[str]:
    problems: list[str] = []
    seen: dict[str, int] = {}

    for q in questions:
        if q.id in seen:
            problems.append(
                f"строка {q.line}: идентификатор {q.id} уже занят (строка {seen[q.id]}). "
                f"Идентификаторы стабильны: по ним считается сводка и собираются наборы"
            )
        seen[q.id] = q.line

        if not q.prompt:
            problems.append(f"строка {q.line}: у вопроса {q.id} пустая формулировка")

        if q.kind == "mc":
            if not 2 <= len(q.options) <= 6:
                problems.append(
                    f"строка {q.line}: у {q.id} {len(q.options)} вариантов, нужно от 2 до 6"
                )
            correct = [o for o in q.options if o.correct]
            if len(correct) != 1:
                problems.append(
                    f"строка {q.line}: у {q.id} отмечено верных вариантов: {len(correct)}, нужен ровно один"
                )
            texts = [o.text.casefold() for o in q.options]
            if len(set(texts)) != len(texts):
                problems.append(f"строка {q.line}: у {q.id} повторяются варианты")
        else:
            if not q.reference:
                problems.append(
                    f"строка {q.line}: у открытого вопроса {q.id} нет строки «{FIELD_REFERENCE}»"
                )

    return problems


def load_bank(path: Path) -> Bank:
    """Прочитать банк с диска. Кидает BankError, если он непригоден."""
    bank, problems = parse_bank(path.read_text(encoding="utf-8"), path=path)
    if problems:
        joined = "\n  ".join(problems)
        raise BankError(f"{path}: банк не разобран:\n  {joined}")
    return bank


def load_banks(directory: Path) -> dict[str, Bank]:
    """Все банки каталога, ключ — слаг лекции. Кидает на первом непригодном.

    Строгий вариант — для командной строки и линтера, где ошибка должна
    останавливать работу.
    """
    banks, errors = scan_banks(directory)
    if errors:
        path, message = next(iter(errors.items()))
        raise BankError(f"{path}: {message}")
    return banks


def scan_banks(directory: Path) -> tuple[dict[str, Bank], dict[str, str]]:
    """Разобрать каталог, вернув отдельно годные банки и отдельно поломки.

    Сервис читает банки этой функцией, а не строгой: опечатка в банке седьмой
    лекции не должна мешать провести пятиминутку по первой. Поломка не
    замалчивается — она возвращается наружу, попадает в лог, в /healthz и на
    страницу преподавателя, а создать пятиминутку по такой лекции нельзя,
    потому что её просто нет в списке годных.
    """
    banks: dict[str, Bank] = {}
    errors: dict[str, str] = {}

    for path in sorted(directory.glob("*.md")):
        if path.name.upper().startswith("README"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors[path.name] = f"файл не читается: {exc}"
            continue

        bank, problems = parse_bank(text, path=path)
        if problems:
            errors[path.name] = "; ".join(problems[:5]) + (
                f" (и ещё {len(problems) - 5})" if len(problems) > 5 else ""
            )
            continue
        if bank.lecture in banks:
            errors[path.name] = f"лекция {bank.lecture} уже описана в {banks[bank.lecture].path}"
            continue
        banks[bank.lecture] = bank

    return banks, errors
