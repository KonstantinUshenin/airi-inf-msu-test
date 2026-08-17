"""Сборка читаемого контекста семинара для LLM-ревью.

Ноутбук в виде JSON модель читает плохо: половина токенов уходит на кавычки и
служебные поля. Здесь `.ipynb` разворачивается в markdown с нумерацией ячеек,
чтобы в замечании можно было сослаться на «ячейку 17».

Модуль не ходит в сеть и не зависит от сторонних пакетов.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Исторически файлы семинара назывались lecture/question/answer, сейчас —
# demo/tasks/solutions. Поддерживаем оба имени, чтобы ревью работало и на
# старых ветках.
DEMO_NAMES = ("demo.ipynb", "lecture.ipynb")
TASKS_NAMES = ("tasks.md", "question.md")
SOLUTIONS_NAMES = ("solutions.md", "answer.md")


def _first_existing(directory: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = directory / name
        if candidate.exists():
            return candidate
    return None


def render_notebook(path: Path) -> str:
    """`.ipynb` → markdown с нумерацией ячеек и выводом."""
    nb = json.loads(path.read_text(encoding="utf-8"))
    out: list[str] = []
    for index, cell in enumerate(nb.get("cells", []), start=1):
        source = "".join(cell.get("source", [])).rstrip()
        kind = cell.get("cell_type")
        if kind == "markdown":
            out.append(f"<!-- ячейка {index}: markdown -->\n{source}")
        elif kind == "code":
            lang = "bash" if source.lstrip().startswith("%%bash") else "python"
            out.append(f"<!-- ячейка {index}: код -->\n```{lang}\n{source}\n```")
            texts = []
            for output in cell.get("outputs", []):
                if "text" in output:
                    texts.append("".join(output["text"]))
                data = output.get("data", {})
                if "text/plain" in data:
                    texts.append("".join(data["text/plain"]))
            printed = "".join(texts).strip()
            if printed:
                if len(printed) > 1500:
                    printed = printed[:1500] + "\n…вывод обрезан…"
                out.append(f"<!-- вывод ячейки {index} -->\n```\n{printed}\n```")
    return "\n\n".join(out)


def seminar_number(directory: Path) -> str | None:
    match = re.search(r"(\d+)", directory.name)
    return str(int(match.group(1))) if match else None


def plan_rows(repo: Path) -> dict[str, str]:
    """Строки таблицы плана из `seminars/README.md`, ключ — номер семинара."""
    readme = repo / "seminars" / "README.md"
    if not readme.exists():
        return {}
    rows: dict[str, str] = {}
    for line in readme.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells:
            continue
        match = re.match(r"^\[?(\d+)\]?", cells[0])
        if match:
            rows[str(int(match.group(1)))] = line.strip()
    return rows


def other_seminars_index(repo: Path, exclude: set[str]) -> str:
    """Короткий индекс соседних семинаров: номер, каталог, заголовки разделов.

    Нужен, чтобы ревьюер видел, что уже разобрано рядом, и ловил дубли и
    понятия, использованные раньше, чем объяснены.
    """
    seminars_dir = repo / "seminars"
    if not seminars_dir.exists():
        return ""
    blocks: list[str] = []
    for directory in sorted(p for p in seminars_dir.iterdir() if p.is_dir()):
        number = seminar_number(directory)
        if number is None or number in exclude:
            continue
        demo = _first_existing(directory, DEMO_NAMES)
        if demo is None:
            continue
        headings = re.findall(
            r"^#{1,3} .+$", render_notebook(demo), flags=re.MULTILINE
        )
        headings = [h for h in headings if not h.startswith("#### ")]
        blocks.append(
            f"### Семинар {number} (`{directory.name}`)\n" + "\n".join(headings[:25])
        )
    return "\n\n".join(blocks)


def build_seminar_block(directory: Path) -> str:
    """Полный текст одного семинара: микро-лекция, задачи, решения."""
    parts: list[str] = []
    demo = _first_existing(directory, DEMO_NAMES)
    tasks = _first_existing(directory, TASKS_NAMES)
    solutions = _first_existing(directory, SOLUTIONS_NAMES)
    images = sorted(p.name for p in (directory / "images").glob("*.svg"))

    parts.append(f"## Семинар: `{directory.as_posix()}`")
    parts.append(
        "Схемы в `images/`: " + (", ".join(images) if images else "нет ни одной")
    )
    if demo:
        parts.append(f"### Микро-лекция `{demo.name}`\n\n{render_notebook(demo)}")
    if tasks:
        parts.append(
            f"### Задачи `{tasks.name}`\n\n{tasks.read_text(encoding='utf-8')}"
        )
    if solutions:
        parts.append(
            f"### Решения `{solutions.name}`\n\n"
            f"{solutions.read_text(encoding='utf-8')}"
        )
    return "\n\n".join(parts)


def build_context(repo: Path, seminar_dirs: list[Path]) -> str:
    """Материалы на ревью + план курса + индекс соседних семинаров."""
    numbers = {n for n in (seminar_number(d) for d in seminar_dirs) if n}
    rows = plan_rows(repo)
    chunks: list[str] = []

    plan_lines = [rows[n] for n in sorted(numbers, key=int) if n in rows]
    if plan_lines:
        chunks.append(
            "# Что обещано планом курса для этих семинаров\n\n"
            "| # | Блок | Тема | Содержание | Домашка | «Забив» | Ревью |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n" + "\n".join(plan_lines)
        )

    chunks.append(
        "# Материалы, которые надо отревьюить\n\n"
        + "\n\n".join(build_seminar_block(d) for d in seminar_dirs)
    )

    index = other_seminars_index(repo, numbers)
    if index:
        chunks.append(
            "# Соседние семинары в репозитории (только оглавления, для поиска "
            "дублей и нарушенного порядка тем)\n\n" + index
        )
    return "\n\n".join(chunks)
