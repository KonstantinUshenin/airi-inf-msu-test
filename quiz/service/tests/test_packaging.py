"""Проверки упаковки — ровно те, что ломались не на моей машине, а на сервере
и в CI.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVICE = ROOT / "quiz" / "service"


def test_linter_runs_without_service_dependencies():
    """Первый шаг CI — линтер, и он идёт ДО установки fastapi.

    Системный python3 их не знает, поэтому запуск под ним воспроизводит CI
    точнее, чем импорт внутри тестового окружения.
    """
    probe = subprocess.run(
        [sys.executable, "-c", "import fastapi"], capture_output=True, text=True
    )
    system = "/usr/bin/python3"
    interpreter = system if probe.returncode == 0 and Path(system).exists() else sys.executable

    result = subprocess.run(
        [interpreter, str(ROOT / "tools" / "lint_quiz_banks.py"), "--stats"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert "ModuleNotFoundError" not in result.stderr, result.stderr
    assert result.returncode == 0, result.stdout + result.stderr


def test_module_entrypoint_exists():
    """systemd-юнит роли `quiz` запускает именно `python -m quizapp`."""
    assert (SERVICE / "quizapp" / "__main__.py").exists()
    result = subprocess.run(
        [sys.executable, "-m", "quizapp", "--help"], capture_output=True, text=True, cwd=SERVICE
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "serve" in result.stdout


def test_unit_and_readme_agree_on_the_entrypoint():
    """Роль живёт в другом репозитории — сверяем команду хотя бы с README."""
    readme = (ROOT / "quiz" / "README.md").read_text(encoding="utf-8")
    assert "python -m quizapp serve" in readme or "python3 -m quizapp serve" in readme


def test_healthz_reports_the_deployed_revision():
    """Иначе «доехал ли деплой» проверяется только гаданием: правки вроде
    порядка вариантов в ответах сервиса никак не видны."""
    import subprocess

    from quizapp.config import checkout_revision

    rev = checkout_revision()
    assert rev, "сервис запущен из git-чекаута, версия должна читаться"
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT
    ).stdout.strip()
    assert head.startswith(rev)
