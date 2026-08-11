"""Линтер банков. Он существует затем, чтобы хрупкий markdown ломался в CI,
а не перед аудиторией, — значит и проверять его надо на поломках.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from lint_quiz_banks import main as lint_main  # noqa: E402

from conftest import make_bank_text  # noqa: E402


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "10-encoding.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_full_bank_passes(tmp_path, capsys):
    assert lint_main([str(write(tmp_path, make_bank_text()))]) == 0
    assert "ERROR" not in capsys.readouterr().out


def test_small_bank_fails_on_counts(tmp_path, capsys):
    assert lint_main([str(write(tmp_path, make_bank_text(n_mc=5, n_open=1)))]) == 1
    out = capsys.readouterr().out
    assert "вопросов с вариантами 5" in out
    assert "открытых вопросов 1" in out


def test_broken_markup_fails_with_a_line_number(tmp_path, capsys):
    text = make_bank_text().replace("- [x] вариант A-0", "- [ ] вариант A-0", 1)
    assert lint_main([str(write(tmp_path, text))]) == 1
    out = capsys.readouterr().out
    assert "верных вариантов: 0" in out
    assert "строка " in out


def test_format_question_option_is_refused(tmp_path, capsys):
    # У вопроса 0 верный вариант — A, поэтому B можно испортить, не сломав
    # правило «ровно один верный».
    text = make_bank_text().replace("- [ ] вариант B-0", "- [ ] Все перечисленное", 1)
    assert lint_main([str(write(tmp_path, text))]) == 1
    assert "проверяет формат, а не лекцию" in capsys.readouterr().out


def test_long_correct_option_is_only_a_warning(tmp_path, capsys):
    text = make_bank_text().replace(
        "- [x] вариант A-0",
        "- [x] очень подробный и обстоятельный вариант, который сразу видно издалека",
        1,
    )
    assert lint_main([str(write(tmp_path, text))]) == 0
    assert "заметно длиннее" in capsys.readouterr().out


def test_missing_criterion_is_only_a_warning(tmp_path, capsys):
    text = make_bank_text().replace("**Засчитывать, если:** упомянута суть номер 0.", "", 1)
    assert lint_main([str(write(tmp_path, text))]) == 0
    assert "судья останется без критерия" in capsys.readouterr().out


def test_missing_file_is_an_error(tmp_path, capsys):
    assert lint_main([str(tmp_path / "нет-такого.md")]) == 1
    assert "файла нет" in capsys.readouterr().out


def test_two_banks_for_one_lecture_are_refused(tmp_path, capsys):
    first = tmp_path / "a.md"
    second = tmp_path / "b.md"
    first.write_text(make_bank_text(), encoding="utf-8")
    second.write_text(make_bank_text(), encoding="utf-8")
    assert lint_main([str(first), str(second)]) == 1
    assert "уже описана" in capsys.readouterr().out
