"""Судья: разбор ответа модели, сборка запроса и то, что сбой провайдера
никого не роняет.
"""

from __future__ import annotations

import pytest

from quizapp.judge import Judge, build_prompt, parse_verdict


def test_parses_plain_json():
    assert parse_verdict('{"correct": true, "rationale": "по сути верно"}') == (True, "по сути верно")


def test_parses_json_in_a_fence():
    raw = '```json\n{"correct": false, "rationale": "нет главного"}\n```'
    assert parse_verdict(raw) == (False, "нет главного")


def test_parses_json_with_chatter_around():
    raw = 'Вот вердикт:\n{"correct": true, "rationale": "ок"}\nНадеюсь, помог.'
    assert parse_verdict(raw) == (True, "ок")


def test_refuses_answer_without_verdict():
    with pytest.raises(ValueError, match="correct"):
        parse_verdict('{"rationale": "не понял вопроса"}')


def test_refuses_answer_without_json():
    with pytest.raises(ValueError, match="нет объекта JSON"):
        parse_verdict("по-моему верно")


def test_prompt_carries_reference_and_criterion():
    prompt = build_prompt(
        question="Что такое BOM?", reference="метка кодировки",
        credit_if="упомянуто первое поле", answer="это метка",
    )
    assert "Что такое BOM?" in prompt
    assert "метка кодировки" in prompt
    assert "упомянуто первое поле" in prompt
    assert "это метка" in prompt


def test_empty_answer_is_shown_as_empty():
    assert "(пусто)" in build_prompt(question="q", reference="r", credit_if="", answer="   ")


@pytest.mark.anyio
async def test_provider_failure_requeues_and_does_not_raise(settings, store, big_bank, monkeypatch):
    quiz = store.create_quiz("10-encoding", "Кодировки")
    token = store.issue_tickets(quiz.id, 1)[0]
    attempt = store.redeem(
        token, login="i", full_name="И", is_test=False,
        questions=[("q-open-000", "open")], timeout_sec=None,
    )
    answer_id = store.answers_for(attempt.id)[0]["id"]
    store.record_answer(attempt.id, "q-open-000", text="мой ответ")
    store.enqueue_judgement(answer_id)

    judge = Judge(settings, store, {"10-encoding": big_bank})

    async def boom(_prompt):
        raise RuntimeError("провайдер лежит")

    monkeypatch.setattr(judge, "ask", boom)
    assert await judge.process_one() is True

    row = store.judgements_for(attempt.id)[answer_id]
    assert row["status"] == "queued"  # вернулось в очередь, а не потерялось
    assert "провайдер лежит" in row["error"]


@pytest.mark.anyio
async def test_verdict_lands_on_the_answer(settings, store, big_bank, monkeypatch):
    quiz = store.create_quiz("10-encoding", "Кодировки")
    token = store.issue_tickets(quiz.id, 1)[0]
    attempt = store.redeem(
        token, login="i", full_name="И", is_test=False,
        questions=[("q-open-000", "open")], timeout_sec=None,
    )
    answer_id = store.answers_for(attempt.id)[0]["id"]
    store.record_answer(attempt.id, "q-open-000", text="мой ответ")
    store.enqueue_judgement(answer_id)

    judge = Judge(settings, store, {"10-encoding": big_bank})

    async def ok(prompt):
        assert "эталонный ответ номер 0" in prompt
        return True, "засчитано по смыслу"

    monkeypatch.setattr(judge, "ask", ok)
    assert await judge.process_one() is True
    assert await judge.process_one() is False  # очередь пуста

    row = store.answers_for(attempt.id)[0]
    assert row["is_correct"] == 1
    assert store.judgements_for(attempt.id)[answer_id]["rationale"] == "засчитано по смыслу"


@pytest.fixture
def anyio_backend():
    return "asyncio"
