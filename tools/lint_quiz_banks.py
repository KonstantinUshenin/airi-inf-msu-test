#!/usr/bin/env python3
"""Линтер банков вопросов: проверяет `quiz/banks/*.md` на пригодность к работе.

    python3 tools/lint_quiz_banks.py                    # все банки
    python3 tools/lint_quiz_banks.py quiz/banks/10-encoding.md
    python3 tools/lint_quiz_banks.py --stats            # ещё и размеры банков

Банк хранится в markdown, потому что его правят люди в pull request
(`docs/adr/0007`). Плата за это — хрупкий парсер с молчаливыми отказами,
и линтер существует ровно затем, чтобы отказ был громким и в CI, а не перед
аудиторией с идущим таймером.

Разбор здесь не свой: используется тот же `quizapp.bank`, который читает сервис.
Иначе линтер проверял бы не то, что потом покажут студентам.

Выход: 0 — нарушений нет, 1 — есть. Предупреждения (WARN) на код возврата
не влияют.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "quiz" / "service"))

from quizapp.bank import Bank, parse_bank  # noqa: E402

BANKS_DIR = ROOT / "quiz" / "banks"

MIN_MC = 40
MIN_OPEN = 10
MIN_PROMPT_CHARS = 20

# «Все перечисленное» и подобное — вопрос про формат, а не про лекцию:
# такие варианты угадываются без знания предмета.
FORBIDDEN_OPTIONS = (
    "все перечисленное",
    "все перечисленные",
    "всё перечисленное",
    "все вышеперечисленное",
    "все ответы верны",
    "ни один из перечисленных",
    "ни один из вариантов",
    "нет верного ответа",
    "все варианты верны",
)

# Насколько верный вариант может быть длиннее среднего неверного, прежде чем
# его станет видно, не читая вопрос.
LENGTH_TELL_RATIO = 1.8


def check_bank(bank: Bank, problems: list[str]) -> tuple[list[str], list[str]]:
    errors = list(problems)
    warns: list[str] = []

    if len(bank.mc) < MIN_MC:
        errors.append(
            f"вопросов с вариантами {len(bank.mc)}, нужно хотя бы {MIN_MC}: "
            f"иначе наборы студентов начнут заметно пересекаться"
        )
    if len(bank.open) < MIN_OPEN:
        errors.append(f"открытых вопросов {len(bank.open)}, нужно хотя бы {MIN_OPEN}")

    for q in bank.questions:
        if len(q.prompt) < MIN_PROMPT_CHARS:
            warns.append(f"{q.id}: формулировка короче {MIN_PROMPT_CHARS} символов")
        if not q.slide:
            warns.append(f"{q.id}: не указан слайд («> Слайд: …») — нечем подкрепить разбор")

        if q.kind == "mc":
            for opt in q.options:
                low = opt.text.strip().casefold().rstrip(".")
                if low in FORBIDDEN_OPTIONS:
                    errors.append(f"{q.id}: вариант «{opt.text}» проверяет формат, а не лекцию")
            correct = [o for o in q.options if o.correct]
            others = [o for o in q.options if not o.correct]
            if correct and others:
                avg = sum(len(o.text) for o in others) / len(others)
                if avg and len(correct[0].text) > avg * LENGTH_TELL_RATIO:
                    warns.append(
                        f"{q.id}: верный вариант заметно длиннее остальных — его видно, не читая вопрос"
                    )
        else:
            if not q.credit_if:
                warns.append(
                    f"{q.id}: нет строки «**Засчитывать, если:**» — судья останется без критерия"
                )

    return errors, warns


def lint_path(path: pathlib.Path, *, stats: bool) -> bool:
    bank, problems = parse_bank(path.read_text(encoding="utf-8"), path=path)
    errors, warns = check_bank(bank, problems)

    for message in errors:
        print(f"{path}: ERROR {message}")
    for message in warns:
        print(f"{path}: WARN  {message}")
    if stats:
        print(
            f"{path}: {len(bank.mc)} с вариантами, {len(bank.open)} открытых, "
            f"лекция {bank.lecture or '?'}"
        )
    if not errors and not warns and not stats:
        print(f"{path}: ок ({len(bank.questions)} вопросов)")
    return not errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Проверка банков вопросов")
    parser.add_argument("paths", nargs="*", type=pathlib.Path)
    parser.add_argument("--stats", action="store_true", help="печатать размеры банков")
    args = parser.parse_args(argv)

    paths = args.paths or sorted(p for p in BANKS_DIR.glob("*.md") if not p.name.upper().startswith("README"))
    if not paths:
        print(f"в {BANKS_DIR} нет банков — проверять нечего")
        return 0

    ok = True
    lectures: dict[str, pathlib.Path] = {}
    for path in paths:
        if not path.exists():
            print(f"{path}: ERROR файла нет")
            ok = False
            continue
        ok &= lint_path(path, stats=args.stats)
        bank, _ = parse_bank(path.read_text(encoding="utf-8"), path=path)
        if bank.lecture:
            if bank.lecture in lectures:
                print(f"{path}: ERROR лекция {bank.lecture} уже описана в {lectures[bank.lecture]}")
                ok = False
            lectures[bank.lecture] = path

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
