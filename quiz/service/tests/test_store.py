"""Хранилище: билеты, попытки, очередь судейства, аналитика."""

from __future__ import annotations

import pytest

from quizapp.store import StoreError, normalize_token, pretty_token

QUESTIONS = [("q-mc-000", "mc"), ("q-mc-001", "mc"), ("q-open-000", "open")]


def _quiz(store, **kw):
    return store.create_quiz("10-encoding", "Кодировки", **kw)


def test_tokens_are_unambiguous_on_paper(store):
    quiz = _quiz(store)
    for token in store.issue_tickets(quiz.id, 50):
        assert len(token) == 8
        assert not set(token) & set("01ILOU")
        assert normalize_token(pretty_token(token)) == token


def test_redeem_creates_attempt_and_answers(store):
    quiz = _quiz(store)
    token = store.issue_tickets(quiz.id, 1)[0]
    attempt = store.redeem(
        token, login="ivanov", full_name="Иванов Иван", is_test=False,
        questions=QUESTIONS, timeout_sec=120, now=1000.0,
    )
    assert attempt.deadline_at == 1120.0
    rows = store.answers_for(attempt.id)
    assert [r["question_id"] for r in rows] == [q for q, _ in QUESTIONS]
    assert all(r["answered_at"] is None for r in rows)
    assert all(r["shown_at"] == 1000.0 for r in rows)


def test_unknown_ticket_is_refused(store):
    with pytest.raises(StoreError, match="не выдавался"):
        store.redeem("ZZZZZZZZ", login="a", full_name="A", is_test=False,
                     questions=QUESTIONS, timeout_sec=None)


def test_used_ticket_is_refused_for_another_person(store):
    quiz = _quiz(store)
    token = store.issue_tickets(quiz.id, 1)[0]
    store.redeem(token, login="ivanov", full_name="Иванов", is_test=False,
                 questions=QUESTIONS, timeout_sec=None)
    with pytest.raises(StoreError, match="уже использован"):
        store.redeem(token, login="petrov", full_name="Петров", is_test=False,
                     questions=QUESTIONS, timeout_sec=None)


def test_second_ticket_returns_the_same_attempt(store):
    """Студент, подобравший второй билет, не начинает попытку заново."""
    quiz = _quiz(store)
    first, second = store.issue_tickets(quiz.id, 2)
    a = store.redeem(first, login="ivanov", full_name="Иванов", is_test=False,
                     questions=QUESTIONS, timeout_sec=None)
    b = store.redeem(second, login="ivanov", full_name="Иванов", is_test=False,
                     questions=QUESTIONS, timeout_sec=None)
    assert a.id == b.id
    assert store.get_ticket(second)["redeemed_at"] is None


def test_changing_an_answer_counts_changes(store):
    quiz = _quiz(store)
    token = store.issue_tickets(quiz.id, 1)[0]
    attempt = store.redeem(token, login="ivanov", full_name="Иванов", is_test=False,
                           questions=QUESTIONS, timeout_sec=None, now=100.0)
    store.record_answer(attempt.id, "q-mc-000", choice=0, is_correct=False, now=105.0)
    store.record_answer(attempt.id, "q-mc-000", choice=1, is_correct=True, now=112.0)
    row = [r for r in store.answers_for(attempt.id) if r["question_id"] == "q-mc-000"][0]
    assert row["changes"] == 1
    assert row["choice"] == 1
    assert row["is_correct"] == 1
    assert row["answered_at"] == 112.0


def test_answer_outside_the_set_is_refused(store):
    quiz = _quiz(store)
    token = store.issue_tickets(quiz.id, 1)[0]
    attempt = store.redeem(token, login="i", full_name="И", is_test=False,
                           questions=QUESTIONS, timeout_sec=None)
    with pytest.raises(StoreError, match="нет в этой попытке"):
        store.record_answer(attempt.id, "q-mc-999", choice=0)


def test_judgement_queue_hands_out_each_task_once(store):
    quiz = _quiz(store)
    token = store.issue_tickets(quiz.id, 1)[0]
    attempt = store.redeem(token, login="i", full_name="И", is_test=False,
                           questions=QUESTIONS, timeout_sec=None)
    answer_id = [r for r in store.answers_for(attempt.id) if r["kind"] == "open"][0]["id"]
    store.enqueue_judgement(answer_id, now=1.0)

    assert store.claim_judgement(now=2.0)["answer_id"] == answer_id
    assert store.claim_judgement(now=2.0) is None  # уже в работе

    store.finish_judgement(answer_id, is_correct=True, rationale="по сути верно", now=3.0)
    row = [r for r in store.answers_for(attempt.id) if r["id"] == answer_id][0]
    assert row["is_correct"] == 1


def test_failed_judgement_returns_to_the_queue_then_gives_up(store):
    quiz = _quiz(store)
    token = store.issue_tickets(quiz.id, 1)[0]
    attempt = store.redeem(token, login="i", full_name="И", is_test=False,
                           questions=QUESTIONS, timeout_sec=None)
    answer_id = [r for r in store.answers_for(attempt.id) if r["kind"] == "open"][0]["id"]
    store.enqueue_judgement(answer_id, now=0.0)

    for attempt_no in range(1, 8):
        row = store.claim_judgement(now=1000.0 * attempt_no)
        if row is None:
            break
        store.finish_judgement(answer_id, is_correct=None, error="провайдер молчит",
                               now=1000.0 * attempt_no)
    failures = store.judge_failures(quiz.id)
    assert len(failures) == 1
    assert failures[0]["status"] == "error"


def test_search_finds_by_name_and_by_ticket(store):
    quiz = _quiz(store)
    tokens = store.issue_tickets(quiz.id, 2)
    store.redeem(tokens[0], login="ivanov", full_name="Иванов Иван", is_test=False,
                 questions=QUESTIONS, timeout_sec=None)
    store.redeem(tokens[1], login="petrov", full_name="Петров Пётр", is_test=False,
                 questions=QUESTIONS, timeout_sec=None)

    assert [r["full_name"] for r in store.attempts_table(quiz.id, "иванов")] == ["Иванов Иван"]
    assert [r["full_name"] for r in store.attempts_table(quiz.id, pretty_token(tokens[1]))] == ["Петров Пётр"]
    assert store.attempts_table(quiz.id, "сидоров") == []


def test_search_is_case_insensitive_for_cyrillic(store):
    """SQLite сворачивает регистр только у латиницы: без своей функции
    «иванов» не нашёл бы «Иванов»."""
    quiz = _quiz(store)
    token = store.issue_tickets(quiz.id, 1)[0]
    store.redeem(token, login="ivanov", full_name="Иванов Иван", is_test=False,
                 questions=QUESTIONS, timeout_sec=None)

    for needle in ("иванов", "ИВАНОВ", "Иванов", "ван"):
        assert len(store.attempts_table(quiz.id, needle)) == 1, needle


def test_search_without_code_characters_does_not_match_everyone(store):
    """Регрессия: заглушка с NUL обрезалась SQLite до «%» и возвращала всех."""
    quiz = _quiz(store)
    tokens = store.issue_tickets(quiz.id, 2)
    store.redeem(tokens[0], login="ivanov", full_name="Иванов Иван", is_test=False,
                 questions=QUESTIONS, timeout_sec=None)
    store.redeem(tokens[1], login="petrov", full_name="Петров Пётр", is_test=False,
                 questions=QUESTIONS, timeout_sec=None)

    # В запросе нет ни одного символа из алфавита кодов — условие по билету
    # не должно превращаться в «совпадает со всем».
    assert store.attempts_table(quiz.id, "щщщ") == []
    assert len(store.attempts_table(quiz.id, "петров")) == 1


def test_question_summary_counts_share_and_median(store):
    quiz = _quiz(store)
    tokens = store.issue_tickets(quiz.id, 2)
    for i, (token, login) in enumerate(zip(tokens, ["a", "b"])):
        attempt = store.redeem(token, login=login, full_name=login.upper(), is_test=False,
                               questions=QUESTIONS, timeout_sec=None, now=0.0)
        store.record_answer(attempt.id, "q-mc-000", choice=0, is_correct=(i == 0), now=10.0 + i)

    row = [r for r in store.question_summary(quiz.id) if r["question_id"] == "q-mc-000"][0]
    assert row["shown"] == 2
    assert row["answered"] == 2
    assert row["correct"] == 1
    assert row["share_correct"] == 0.5
    assert 10.0 <= row["median_time"] <= 11.0
