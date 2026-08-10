#!/usr/bin/env python3
"""Смысловое ревью семинаров моделью DeepSeek.

Скрипт кладёт в промпт критерии из `.github/seminar-review-prompt.md` и полный
текст изменённых семинаров, после чего даёт модели инструменты чтения
репозитория (`tools/repo_tools.py`) и печатает готовый текст ревью.

Два уровня доступа к материалу — намеренно. Семинар на ревью подаётся целиком и
безусловно: ревьюер обязан увидеть то, что ревьюит, а не решать, открывать ли
файл. Всё остальное — план курса в `seminars/README.md`, соседние семинары,
конспекты лекций — модель читает сама по мере надобности: заранее угадать, что
ей понадобится, нельзя, а без этого она не поймает ни дубли между занятиями, ни
расхождение с планом. Флаг `--no-tools` возвращает старое поведение без чтения
файлов и нужен для замера: он показывает, что именно даёт доступ к репозиторию.

Использование в CI:

    python3 tools/review_seminars.py --changed-files changed_files.txt

Локально по каталогам:

    python3 tools/review_seminars.py --seminar "seminars/05-unix-env"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_tools import TOOL_SCHEMA, RepoTools  # noqa: E402
from seminar_context import build_context  # noqa: E402

# По умолчанию — родное API DeepSeek. Через REVIEW_API_URL/REVIEW_API_KEY можно
# отправить те же запросы в любой OpenAI-совместимый шлюз (например, OpenRouter),
# не трогая workflow: модель и промпт остаются теми же.
API_URL = os.environ.get(
    "REVIEW_API_URL", "https://api.deepseek.com/chat/completions"
)
DEFAULT_MODEL = os.environ.get("REVIEW_MODEL", "deepseek-v4-pro")
# Два прохода с раздельными бюджетами пунктов: методист смотрит содержание,
# технический рецензент — исполнимость демки. При одном общем списке
# технические замечания находятся первыми и вытесняют содержательные, которые
# надо думать; замер это подтвердил (см. tools/review_eval/README.md).
DEFAULT_PROMPT = (
    ".github/seminar-review-prompt.md,.github/seminar-review-prompt-tech.md"
)
# Потолок обращений к файлам за одно ревью. Считался по замеру: агент обычно
# укладывается в 4-6 шагов, 10 оставляет запас и не даёт зациклиться.
MAX_TOOL_STEPS = int(os.environ.get("REVIEW_MAX_TOOL_STEPS", "10"))


def changed_seminar_dirs(repo: Path, changed_files: Path) -> list[Path]:
    """Каталоги семинаров, затронутые pull request'ом."""
    dirs: dict[str, Path] = {}
    for line in changed_files.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split("/")
        if len(parts) >= 2 and parts[0] == "seminars":
            directory = repo / parts[0] / parts[1]
            if directory.is_dir():
                dirs[directory.as_posix()] = directory
    return [dirs[k] for k in sorted(dirs)]


def post_chat(payload: dict, *, api_key: str, timeout: int = 900) -> dict:
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:  # ошибку API видно в логах CI целиком
        raise SystemExit(
            f"DeepSeek вернул {error.code}: {error.read().decode('utf-8', 'replace')}"
        )


def call_model(
    prompt: str, *, model: str, api_key: str, temperature: float, timeout: int = 900
) -> str:
    body = post_chat(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": False,
        },
        api_key=api_key,
        timeout=timeout,
    )
    return body["choices"][0]["message"]["content"]


def call_agent(
    prompt: str,
    *,
    repo: Path,
    model: str,
    api_key: str,
    temperature: float,
    max_steps: int = MAX_TOOL_STEPS,
    trace: list[str] | None = None,
) -> str:
    """Ревью с доступом на чтение репозитория.

    Материал семинара всё равно кладём в промпт целиком: гарантия «модель точно
    видела то, что ревьюит» дороже экономии токенов. Инструменты — сверх этого,
    чтобы можно было заглянуть в план курса, соседний семинар или конспект
    лекции по собственному решению.
    """
    tools = RepoTools(repo)
    messages: list[dict] = [{"role": "user", "content": prompt}]
    for _ in range(max_steps):
        body = post_chat(
            {
                "model": model,
                "messages": messages,
                "tools": TOOL_SCHEMA,
                "temperature": temperature,
                "stream": False,
            },
            api_key=api_key,
        )
        message = body["choices"][0]["message"]
        calls = message.get("tool_calls") or []
        messages.append(
            {
                "role": "assistant",
                "content": message.get("content") or "",
                **({"tool_calls": calls} if calls else {}),
            }
        )
        if not calls:
            if trace is not None:
                trace.extend(tools.calls)
            return message.get("content") or ""
        for call in calls:
            function = call.get("function", {})
            try:
                arguments = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id"),
                    "content": tools.dispatch(function.get("name", ""), arguments),
                }
            )
    # Шаги кончились — просим итог тем, что уже прочитано, вместо обрыва.
    messages.append(
        {
            "role": "user",
            "content": "Лимит обращений к файлам исчерпан. Напиши ревью по тому, "
            "что уже прочитал, в требуемом формате.",
        }
    )
    body = post_chat(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        },
        api_key=api_key,
    )
    if trace is not None:
        trace.extend(tools.calls)
    return body["choices"][0]["message"]["content"] or ""


# Заголовки проходов: без них «Итог» методиста оказывается в середине текста,
# сразу перед разделами технического рецензента, и читается как итог всего.
PASS_TITLES = ("## Содержание и методика", "## Техническая проверка")


def join_passes(chunks: list[str]) -> str:
    parts = [c.strip() for c in chunks]
    if len(parts) != len(PASS_TITLES):
        return "\n\n".join(p for p in parts if p)
    return "\n\n".join(
        f"{title}\n\n{body}" for title, body in zip(PASS_TITLES, parts) if body
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="корень репозитория")
    parser.add_argument("--changed-files", help="файл со списком изменённых путей")
    parser.add_argument(
        "--seminar", action="append", default=[], help="каталог семинара (можно много)"
    )
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="файл с критериями")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--out", help="куда записать ревью (по умолчанию stdout)")
    parser.add_argument(
        "--dump-prompt", help="сохранить итоговый промпт (для отладки), без вызова API"
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="без доступа к файлам: только текст семинара в промпте (для замера)",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    seminars = [Path(s) if Path(s).is_absolute() else repo / s for s in args.seminar]
    if args.changed_files:
        seminars += changed_seminar_dirs(repo, Path(args.changed_files))
    seminars = sorted({s.resolve() for s in seminars if s.is_dir()})

    if not seminars:
        print("изменённых семинаров нет — ревью не требуется")
        return 0

    criteria_parts = []
    for part in args.prompt.split(","):
        criteria_path = Path(part.strip())
        if not criteria_path.is_absolute():
            criteria_path = repo / criteria_path
        criteria_parts.append(criteria_path.read_text(encoding="utf-8"))

    # По одному вызову на семинар и на проход: иначе лимит замечаний делится на
    # всех и семинары в конце списка получают ревью по остаточному принципу.
    prompts = {
        seminar: [
            criteria + "\n\n" + build_context(repo, [seminar])
            for criteria in criteria_parts
        ]
        for seminar in seminars
    }

    if args.dump_prompt:
        dump = "\n\n".join(p for parts in prompts.values() for p in parts)
        Path(args.dump_prompt).write_text(dump, encoding="utf-8")
        print(f"промпт сохранён в {args.dump_prompt} ({len(dump)} символов)")
        return 0

    api_key = os.environ.get("REVIEW_API_KEY") or os.environ.get(
        "DEEPSEEK_API_KEY", ""
    )
    if not api_key:
        print("нет DEEPSEEK_API_KEY — ревью пропускаем", file=sys.stderr)
        return 0

    sections: list[str] = []
    for seminar, parts in prompts.items():
        trace: list[str] = []
        chunks = []
        for prompt in parts:
            if args.no_tools:
                chunks.append(
                    call_model(
                        prompt,
                        model=args.model,
                        api_key=api_key,
                        temperature=args.temperature,
                    )
                )
            else:
                chunks.append(
                    call_agent(
                        prompt,
                        repo=repo,
                        model=args.model,
                        api_key=api_key,
                        temperature=args.temperature,
                        trace=trace,
                    )
                )
        review = join_passes(chunks)
        if trace:
            print(f"# файлы, которые смотрел ревьюер: {'; '.join(trace)}",
                  file=sys.stderr)
        header = (
            f"## `{seminar.relative_to(repo).as_posix()}`\n\n"
            if len(prompts) > 1
            else ""
        )
        sections.append(header + review.strip())

    result = "\n\n".join(sections)
    if args.out:
        Path(args.out).write_text(result, encoding="utf-8")
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
