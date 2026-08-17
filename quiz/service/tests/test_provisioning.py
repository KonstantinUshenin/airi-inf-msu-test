"""Автозаведение пятиминуток и билетов из банков.

Появился банк новой лекции — после деплоя всё готово: преподавателю остаётся
поправить настройки и открыть приём. И ровно одна пятиминутка на лекцию.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from quizapp.config import Settings
from quizapp.store import Store, StoreError
from quizapp.web import create_app, provision_from_banks

from conftest import make_bank_text


def test_quiz_and_tickets_appear_for_every_bank(tmp_path, banks_dir, monkeypatch):
    monkeypatch.setenv("QUIZ_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("QUIZ_BANKS_DIR", str(banks_dir))
    monkeypatch.setenv("QUIZ_TEACHER_TOKEN", "t")
    monkeypatch.setenv("QUIZ_SECRET_KEY", "s")
    monkeypatch.setenv("QUIZ_AUTO_TICKETS", "36")
    (banks_dir / "11-hierarchy.md").write_text(make_bank_text(lecture="11-hierarchy"), encoding="utf-8")

    settings = Settings()
    with TestClient(create_app(settings)):
        db = Store(settings.db_path)
        lectures = sorted(q.lecture for q in db.list_quizzes())
        assert lectures == ["10-encoding", "11-hierarchy"]
        for quiz in db.list_quizzes():
            assert quiz.state == "closed", "открывать должен человек, а не выкатка"
            assert quiz.mode == "practice"
            assert len(db.tickets_for(quiz.id)) == 36
        db.close()


def test_provisioning_is_idempotent_and_keeps_teacher_settings(store, big_bank):
    banks = {"10-encoding": big_bank}
    assert provision_from_banks(store, banks, ticket_count=5) == ["10-encoding"]

    quiz = store.quiz_for_lecture("10-encoding")
    store.update_quiz(quiz.id, state="open", mode="graded", timeout_sec=90, touch_timeout=True)

    # Повторный запуск сервиса ничего не пересоздаёт и не откатывает.
    assert provision_from_banks(store, banks, ticket_count=5) == []
    again = store.quiz_for_lecture("10-encoding")
    assert (again.id, again.state, again.mode, again.timeout_sec) == (quiz.id, "open", "graded", 90)
    assert len(store.tickets_for(quiz.id)) == 5


def test_second_quiz_for_the_same_lecture_is_refused(store):
    store.create_quiz("10-encoding", "Кодировки")
    with pytest.raises(StoreError, match="уже есть"):
        store.create_quiz("10-encoding", "Кодировки ещё раз")


def test_api_create_returns_the_existing_quiz_instead_of_a_second_one(teacher):
    first = teacher.post("/api/teacher/quizzes", json={"lecture": "10-encoding"}).json()
    second = teacher.post("/api/teacher/quizzes", json={"lecture": "10-encoding"}).json()
    assert first["id"] == second["id"]


def test_button_create_returns_to_the_existing_quiz(teacher):
    resp = teacher.post("/teacher/quizzes", data={"lecture": "10-encoding"}, follow_redirects=True)
    assert "пятиминутка уже была" in resp.text


# --- миграция старых баз ---------------------------------------------------


def _legacy_store_with_two_quizzes(tmp_path, *, attempts_on):
    """База, заведённая до правила «одна лекция — одна пятиминутка»."""
    db = Store(tmp_path / "quiz.sqlite")
    first = db.create_quiz("01-history", "История")
    with db._lock:  # обходим уникальный индекс, как это выглядело раньше
        db._db.execute("DROP INDEX quiz_one_per_lecture")
        db._db.execute(
            "INSERT INTO quiz(lecture, title, state, mode, timeout_sec, created_at)"
            " VALUES ('01-history', 'История (дубль)', 'closed', 'practice', 120, 1)"
        )
        db._db.commit()
    second = [q for q in db.list_quizzes() if q.id != first.id][0]

    for quiz_id in attempts_on:
        target = first.id if quiz_id == 1 else second.id
        token = db.issue_tickets(target, 1)[0]
        db.redeem(token, login=f"student{target}", full_name="С", is_test=True,
                  questions=[("q-mc-000", "mc")], timeout_sec=None)
    db.close()
    return tmp_path / "quiz.sqlite"


def test_migration_drops_the_empty_duplicate(tmp_path):
    path = _legacy_store_with_two_quizzes(tmp_path, attempts_on=[1])

    db = Store(path)  # повторное открытие = миграция
    quizzes = db.list_quizzes()
    assert len(quizzes) == 1
    assert quizzes[0].title == "История", "оставили ту, где есть ответы"
    db.close()


def test_migration_keeps_the_oldest_when_both_are_empty(tmp_path):
    path = _legacy_store_with_two_quizzes(tmp_path, attempts_on=[])

    db = Store(path)
    quizzes = db.list_quizzes()
    assert len(quizzes) == 1
    assert quizzes[0].title == "История"
    db.close()


def test_migration_refuses_to_choose_between_two_used_quizzes(tmp_path):
    path = _legacy_store_with_two_quizzes(tmp_path, attempts_on=[1, 2])

    with pytest.raises(StoreError, match="несколько пятиминуток с ответами"):
        Store(path)
