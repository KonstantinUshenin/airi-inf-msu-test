"""Командная строка: поднять сервис и завести пятиминутку без curl.

Полный набор операций есть по HTTP (преподавательский токен), но перед лекцией
удобнее одной командой на сервере, без копирования токена в терминал.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bank import BankError, load_banks
from .config import Settings
from .store import Store, pretty_token


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quizapp", description="Пятиминутки")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("serve", help="поднять сервис")
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument("--port", type=int, default=8391)

    sub.add_parser("banks", help="показать банки, которые видит сервис")

    new = sub.add_parser("new", help="завести пятиминутку")
    new.add_argument("lecture")
    new.add_argument("--title", default="")
    new.add_argument("--graded", action="store_true", help="боевой режим: таймер и оценки")
    new.add_argument("--timeout", type=int, default=None)

    state = sub.add_parser("state", help="открыть или закрыть")
    state.add_argument("quiz_id", type=int)
    state.add_argument("value", choices=("open", "closed"))

    tickets = sub.add_parser("tickets", help="выпустить билеты и собрать PDF")
    tickets.add_argument("quiz_id", type=int)
    tickets.add_argument("--count", type=int, default=36)
    tickets.add_argument("--pdf", type=Path, default=None)

    args = parser.parse_args(argv)
    settings = Settings()

    if args.cmd == "serve":
        import uvicorn

        uvicorn.run(
            "quizapp.web:create_app", factory=True, host=args.host, port=args.port, log_level="info"
        )
        return 0

    if args.cmd == "banks":
        try:
            banks = load_banks(settings.banks_dir)
        except BankError as exc:
            print(exc, file=sys.stderr)
            return 1
        if not banks:
            print(f"в {settings.banks_dir} нет банков")
            return 1
        for slug, bank in sorted(banks.items()):
            print(f"{slug}: {len(bank.mc)} с вариантами, {len(bank.open)} открытых — {bank.title}")
        return 0

    store = Store(settings.db_path)

    if args.cmd == "new":
        banks = load_banks(settings.banks_dir)
        if args.lecture not in banks:
            print(f"нет банка для {args.lecture}; есть: {', '.join(sorted(banks))}", file=sys.stderr)
            return 1
        quiz = store.create_quiz(
            args.lecture,
            args.title or banks[args.lecture].title,
            mode="graded" if args.graded else "practice",
            timeout_sec=args.timeout or settings.default_timeout_sec,
        )
        print(f"пятиминутка {quiz.id}: {quiz.lecture}, режим {quiz.mode}, закрыта")
        return 0

    if args.cmd == "state":
        quiz = store.update_quiz(args.quiz_id, state=args.value)
        print(f"пятиминутка {quiz.id}: {quiz.state}")
        return 0

    if args.cmd == "tickets":
        tokens = store.issue_tickets(args.quiz_id, args.count)
        print(f"выпущено билетов: {len(tokens)}")
        for token in tokens:
            print(" ", pretty_token(token))
        if args.pdf:
            from .tickets import build_pdf

            quiz = store.get_quiz(args.quiz_id)
            args.pdf.write_bytes(
                build_pdf(
                    base_url=settings.base_url,
                    tokens=tokens,
                    heading=f"Пятиминутка — {quiz.title or quiz.lecture}",
                )
            )
            print(f"лист на печать: {args.pdf}")
        return 0

    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
