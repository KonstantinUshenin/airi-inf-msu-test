#!/usr/bin/env python3
"""Линтер семинаров: проверяет `seminars/NN-slug/` на соответствие формату курса.

    python3 tools/lint_seminars.py                 # проверить все семинары
    python3 tools/lint_seminars.py seminars/04-git # проверить один
    python3 tools/lint_seminars.py --stats         # ещё и таблица по ячейкам
    python3 tools/lint_seminars.py --changed main  # только семинары, затронутые веткой

Правила описаны в `.claude/skills/seminar-format/SKILL.md`; здесь автоматизирована
та их часть, которую машина проверяет надёжно. Всё, что требует смысла
(«вопрос выводим из демки», «мотивация объясняет зачем»), остаётся человеку.

Выход: 0 — нарушений нет, 1 — есть. Предупреждения (WARN) на код возврата не влияют.
Исключений и списков «известного долга» нет: правило либо соблюдается, либо нет.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

# --- настройки правил -------------------------------------------------------

MAX_CODE_LINES = 8          # содержательных строк кода в одной ячейке
MIN_TASKS_PER_LEVEL = 5
MAX_TASKS_PER_LEVEL = 10

QUESTION_RE = re.compile(r"^#### ❓ \*\*Вопрос\*\*", re.M)
OLD_QUESTION_RE = re.compile(r"^#{2,4} +Вопрос\s*$", re.M)
LEVELS = ("База", "Среднее", "Сложное")
LEVEL_PREFIX = {"База": "B", "Среднее": "M", "Сложное": "H"}


class Report:
    """Накопитель находок. Исключений нет: любая ошибка роняет проверку."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, msg: str, rule: str) -> None:
        self.errors.append(f"{where}: {msg}  [{rule}]")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


# --- вспомогательное --------------------------------------------------------


def code_lines(source: str) -> list[str]:
    """Содержательные строки ячейки: без пустых, комментариев и строки магии."""
    out = []
    for line in source.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("%%"):      # %%bash и подобные — не код ячейки
            continue
        out.append(line)
    return out


# --- проверки ---------------------------------------------------------------


def check_demo(path: pathlib.Path, rep: Report, stats: list) -> None:
    try:
        nb = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        rep.error(str(path), f"не читается как ipynb ({exc})", "broken-ipynb")
        return

    cells = nb.get("cells", [])
    if not cells:
        rep.error(str(path), "в ноутбуке нет ячеек", "broken-ipynb")
        return

    first_md = next((c for c in cells if c["cell_type"] == "markdown"), None)
    if first_md is None or "## Мотивация" not in "".join(first_md["source"]):
        head = "".join(cells[0]["source"])[:60].replace("\n", " ")
        if "Мотивация" not in "".join("".join(c["source"]) for c in cells[:3]):
            rep.error(str(path), f"первые ячейки не содержат блок «## Мотивация» (начало: {head!r})", "motivation")

    whole = "\n".join("".join(c["source"]) for c in cells)
    if not QUESTION_RE.search(whole):
        if OLD_QUESTION_RE.search(whole):
            rep.error(str(path), "вопросы оформлены старым заголовком «### Вопрос» — "
                                 "нужен формат «#### ❓ **Вопрос**» со свёрнутым ответом в <details>", "question-format")
        else:
            rep.error(str(path), "нет ни одного вопроса в формате «#### ❓ **Вопрос**»", "question-format")

    for i, cell in enumerate(cells):
        src = "".join(cell["source"])
        where = f"{path}:ячейка {i}"

        if cell["cell_type"] != "code":
            continue

        lines = code_lines(src)
        stats.append((str(path), i, len(lines)))
        if len(lines) > MAX_CODE_LINES:
            rep.error(where, f"{len(lines)} строк кода, разрешено не более {MAX_CODE_LINES} — разбейте ячейку", "max-code-lines")

        if not src.lstrip().startswith("%%"):
            for line in lines:
                code_part = line.split("#")[0]
                if ";" in code_part and not re.search(r'["\'].*;.*["\']', code_part):
                    rep.error(where, f"несколько операторов через «;» в одной строке: {line.strip()!r}", "semicolon")


def parse_tasks(text: str) -> dict[str, list[str]]:
    """Задачи по уровням: {'База': ['B1', ...], ...}."""
    out: dict[str, list[str]] = {lvl: [] for lvl in LEVELS}
    current = None
    for line in text.split("\n"):
        m = re.match(r"^## (База|Среднее|Сложное)\b", line)   # допускается «## База — 5 задач»
        if m:
            current = m.group(1)
            continue
        m = re.match(r"^### ([BMH]\d+)\.", line)
        if m and current:
            out[current].append(m.group(1))
    return out


def check_tasks(path: pathlib.Path, sol_path: pathlib.Path, rep: Report) -> None:
    text = path.read_text(encoding="utf-8")
    by_level = parse_tasks(text)
    for level in LEVELS:
        ids = by_level[level]
        if not ids:
            rep.error(str(path), f"нет раздела «## {level}» или в нём нет задач", "levels")
            continue
        if not (MIN_TASKS_PER_LEVEL <= len(ids) <= MAX_TASKS_PER_LEVEL):
            rep.error(str(path), f"уровень «{level}»: {len(ids)} задач, нужно "
                                 f"{MIN_TASKS_PER_LEVEL}–{MAX_TASKS_PER_LEVEL}", "tasks-per-level")
        prefix = LEVEL_PREFIX[level]
        wrong = [i for i in ids if not i.startswith(prefix)]
        if wrong:
            rep.error(str(path), f"уровень «{level}»: идентификаторы не с «{prefix}»: {', '.join(wrong)}", "task-ids")

    task_ids = [i for level in LEVELS for i in by_level[level]]
    for tid in task_ids:
        block = re.search(rf"^### {tid}\..*?(?=^### |\Z)", text, re.S | re.M)
        if block and "**need:**" not in block.group(0):
            rep.error(str(path), f"задача {tid}: нет строки «**need:**»", "need")

    if not sol_path.exists():
        rep.error(str(sol_path), "файла с решениями нет", "solutions-missing")
        return
    sol_text = sol_path.read_text(encoding="utf-8")
    sol_ids = re.findall(r"^### ([BMH]\d+)[.\s]*$|^### ([BMH]\d+)\.", sol_text, re.M)
    sol_ids = [a or b for a, b in sol_ids]
    missing = [i for i in task_ids if i not in sol_ids]
    extra = [i for i in sol_ids if i not in task_ids]
    if missing:
        rep.error(str(sol_path), f"нет решений для задач: {', '.join(missing)}", "solutions-missing")
    if extra:
        rep.error(str(sol_path), f"решения без задач: {', '.join(extra)}", "solutions-extra")
    if not missing and not extra and sol_ids != task_ids:
        rep.warn(str(sol_path), "порядок решений не совпадает с порядком задач")


def check_seminar(directory: pathlib.Path, rep: Report, stats: list) -> None:
    if not re.match(r"^\d{2}-[a-z0-9-]+$", directory.name):
        rep.error(str(directory), "имя каталога не по схеме NN-slug (см. ADR 0003)", "dir-name")

    demo = directory / "demo.ipynb"
    tasks = directory / "tasks.md"
    solutions = directory / "solutions.md"

    if demo.exists():
        check_demo(demo, rep, stats)
    else:
        rep.error(str(demo), "нет микро-лекции demo.ipynb", "missing-file")

    if tasks.exists():
        check_tasks(tasks, solutions, rep)
    else:
        rep.error(str(tasks), "нет файла задач tasks.md", "missing-file")


def changed_seminars(base_ref: str, root: pathlib.Path) -> list[pathlib.Path] | None:
    """Каталоги семинаров, затронутых относительно `base_ref`.

    Проверяются ровно те семинары, файлы которых попали в diff, — и никакие
    другие: автор правки отвечает за свой материал, а не за чужой долг.
    Возвращает None, только если diff посчитать не удалось.
    """
    diff = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        cwd=root, capture_output=True, text=True,
    )
    if diff.returncode != 0:            # нет такой ветки / не репозиторий
        print(f"не удалось получить diff против {base_ref}: {diff.stderr.strip()}")
        return None

    files = [f for f in diff.stdout.split("\n") if f.strip()]
    dirs = []
    for f in files:
        parts = pathlib.Path(f).parts
        if len(parts) >= 2 and parts[0] == "seminars" and re.match(r"^\d{2}-", parts[1]):
            d = root / parts[0] / parts[1]
            if d.is_dir() and d not in dirs:
                dirs.append(d)
    return dirs


def main() -> int:
    parser = argparse.ArgumentParser(description="Линтер семинаров курса")
    parser.add_argument("paths", nargs="*", help="каталоги семинаров (по умолчанию — все)")
    parser.add_argument("--stats", action="store_true", help="таблица длин кодовых ячеек")
    parser.add_argument("--changed", metavar="BASE",
                        help="проверять только семинары, затронутые относительно ветки BASE "
                             "(например --changed origin/main); правка правил или самого линтера "
                             "включает полную проверку")
    args = parser.parse_args()

    root = pathlib.Path(__file__).resolve().parent.parent
    all_dirs = sorted(d for d in (root / "seminars").iterdir()
                      if d.is_dir() and re.match(r"^\d{2}-", d.name))

    if args.paths:
        dirs = [pathlib.Path(p).resolve() for p in args.paths]
    elif args.changed:
        dirs = changed_seminars(args.changed, root)
        if dirs is None:                # diff не посчитался — проверяем всё, чтобы не пропустить
            dirs = all_dirs
        elif not dirs:
            print(f"семинары не затронуты относительно {args.changed} — проверять нечего")
            return 0
    else:
        dirs = all_dirs

    if not dirs:
        print("семинаров не найдено")
        return 0

    rep = Report()
    stats: list = []
    for d in dirs:
        check_seminar(d, rep, stats)

    if args.stats and stats:
        print("Длины кодовых ячеек (строк кода):")
        for path, idx, n in stats:
            mark = "  !" if n > MAX_CODE_LINES else "   "
            print(f"{mark} {path}:ячейка {idx}: {n}")
        print()

    for w in rep.warnings:
        print(f"WARN  {w}")
    for e in rep.errors:
        print(f"ERROR {e}")

    checked = ", ".join(d.name for d in dirs)
    print(f"\nПроверено семинаров: {len(dirs)} ({checked}); "
          f"ошибок: {len(rep.errors)}, предупреждений: {len(rep.warnings)}")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
