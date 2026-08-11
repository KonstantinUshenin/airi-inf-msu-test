"""Точка входа для `python -m quizapp` — её зовёт systemd-юнит роли `quiz`."""

from .cli import main

raise SystemExit(main())
