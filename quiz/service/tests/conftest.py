from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quizapp.bank import parse_bank  # noqa: E402
from quizapp.config import Settings  # noqa: E402
from quizapp.store import Store  # noqa: E402

SMALL_BANK = """\
# Банк вопросов — лекция 10 «Кодировки»

<!-- quiz-bank: lecture=10-encoding -->

## С вариантами

### q-mc-utf8-ya

Сколько байт занимает буква «я» в UTF-8?

- [ ] 1
- [x] 2
- [ ] 3
- [ ] 4

> Слайд: Encoding → UTF-8

### q-mc-ascii-range

Какой диапазон кодов занимает ASCII?

- [x] 0–127
- [ ] 0–255
- [ ] 1–128

> Слайд: Encoding → ASCII

## Открытые

### q-open-bom

Что такое BOM и почему из-за него ломается чтение CSV?

**Эталон:** BOM помечает кодировку в начале файла; парсер, который его не ждёт,
читает его как часть первого поля, поэтому имя первой колонки не совпадает.

**Засчитывать, если:** сказано, что BOM попадает в первое поле или ломает имя
первой колонки.

> Слайд: Encoding → BOM
"""


def make_bank_text(*, lecture: str = "10-encoding", n_mc: int = 40, n_open: int = 10) -> str:
    """Синтетический банк нужного размера — для проверок, где важен объём."""
    lines = [f"# Банк вопросов — {lecture}", "", f"<!-- quiz-bank: lecture={lecture} -->", "", "## С вариантами", ""]
    for i in range(n_mc):
        lines += [
            f"### q-mc-{i:03d}",
            "",
            f"Вопрос с вариантами номер {i}, достаточно длинная формулировка?",
            "",
            f"- [{'x' if i % 3 == 0 else ' '}] вариант A-{i}",
            f"- [{'x' if i % 3 == 1 else ' '}] вариант B-{i}",
            f"- [{'x' if i % 3 == 2 else ' '}] вариант C-{i}",
            "",
            f"> Слайд: раздел {i % 5}",
            "",
        ]
    lines += ["## Открытые", ""]
    for i in range(n_open):
        lines += [
            f"### q-open-{i:03d}",
            "",
            f"Открытый вопрос номер {i}, объясните своими словами суть?",
            "",
            f"**Эталон:** эталонный ответ номер {i}, достаточно подробный.",
            "",
            f"**Засчитывать, если:** упомянута суть номер {i}.",
            "",
            f"> Слайд: раздел {i % 5}",
            "",
        ]
    return "\n".join(lines)


@pytest.fixture
def small_bank():
    bank, problems = parse_bank(SMALL_BANK)
    assert problems == [], problems
    return bank


@pytest.fixture
def big_bank():
    bank, problems = parse_bank(make_bank_text())
    assert problems == [], problems
    return bank


@pytest.fixture
def banks_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "banks"
    directory.mkdir()
    (directory / "10-encoding.md").write_text(make_bank_text(), encoding="utf-8")
    return directory


@pytest.fixture
def store(tmp_path: Path) -> Store:
    db = Store(tmp_path / "quiz.sqlite")
    yield db
    db.close()


@pytest.fixture
def settings(tmp_path: Path, banks_dir: Path, monkeypatch) -> Settings:
    for name in list(__import__("os").environ):
        if name.startswith("QUIZ_") or name in ("REVIEW_API_KEY", "DEEPSEEK_API_KEY", "REVIEW_MODEL"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("QUIZ_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("QUIZ_BANKS_DIR", str(banks_dir))
    monkeypatch.setenv("QUIZ_TEACHER_TOKEN", "secret-teacher-token")
    monkeypatch.setenv("QUIZ_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("QUIZ_AUTH_MODE", "test")
    monkeypatch.setenv("QUIZ_JUDGE_ENABLED", "0")
    monkeypatch.setenv("QUIZ_BASE_URL", "http://testserver")
    # Пятиминутки заводятся автоматически, а билеты в большинстве тестов
    # выпускаются явно и по счёту — поэтому автовыпуск здесь выключен.
    # У него свои тесты, где он включается намеренно.
    monkeypatch.setenv("QUIZ_AUTO_TICKETS", "0")
    return Settings()


@pytest.fixture
def client(settings: Settings):
    from fastapi.testclient import TestClient

    from quizapp.web import create_app

    app = create_app(settings)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def teacher(client):
    client.cookies.set("quiz_teacher", "secret-teacher-token")
    return client
