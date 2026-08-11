"""Набор обязан быть воспроизводимым: перезагрузка страницы, возврат после
потери сети и пересчёт задним числом должны давать одни и те же вопросы.
"""

from __future__ import annotations

import pytest

from quizapp.bank import parse_bank
from quizapp.selection import option_order, pick_question_ids

from conftest import make_bank_text


def test_same_login_same_set(big_bank):
    first = pick_question_ids(big_bank, "ivanov")
    second = pick_question_ids(big_bank, "ivanov")
    assert first == second


def test_set_shape(big_bank):
    ids = pick_question_ids(big_bank, "ivanov")
    assert len(ids) == 5
    assert sum(1 for i in ids if i.startswith("q-mc-")) == 4
    assert sum(1 for i in ids if i.startswith("q-open-")) == 1
    assert ids[-1].startswith("q-open-")
    assert len(set(ids)) == 5


def test_neighbours_get_different_sets(big_bank):
    sets = {tuple(pick_question_ids(big_bank, f"student-{i}")) for i in range(30)}
    # Совпадения возможны, но 30 одинаковых наборов означали бы, что логин
    # в выборку не попадает вовсе.
    assert len(sets) > 20


def test_different_lecture_gives_different_set():
    a, _ = parse_bank(make_bank_text(lecture="10-encoding"))
    b, _ = parse_bank(make_bank_text(lecture="11-hierarchy"))
    assert pick_question_ids(a, "ivanov") != pick_question_ids(b, "ivanov")


def test_option_order_is_stable_and_a_permutation(small_bank):
    q = small_bank.by_id["q-mc-utf8-ya"]
    order = option_order(q)
    assert order == option_order(q)
    assert sorted(order) == list(range(len(q.options)))


def test_bank_too_small_is_refused():
    bank, _ = parse_bank(make_bank_text(n_mc=3, n_open=1))
    with pytest.raises(ValueError, match="вопросов с вариантами"):
        pick_question_ids(bank, "ivanov")


def test_set_spreads_across_slides(big_bank):
    """Пять вопросов не должны кучковаться на одном разделе лекции."""
    for i in range(40):
        ids = pick_question_ids(big_bank, f"student-{i}")
        slides = [big_bank.by_id[q].slide for q in ids if q.startswith("q-mc-")]
        assert len(set(slides)) == len(slides), (i, slides)


def test_small_bank_still_yields_a_set():
    """Если разных слайдов меньше, чем вопросов, ограничение отпускается."""
    text = make_bank_text(n_mc=6, n_open=1).replace("> Слайд: раздел 1", "> Слайд: раздел 0")
    text = text.replace("> Слайд: раздел 2", "> Слайд: раздел 0")
    text = text.replace("> Слайд: раздел 3", "> Слайд: раздел 0")
    text = text.replace("> Слайд: раздел 4", "> Слайд: раздел 0")
    bank, problems = parse_bank(text)
    assert problems == []
    ids = pick_question_ids(bank, "ivanov")
    assert len(ids) == 5
    assert len(set(ids)) == 5


def test_spread_is_still_deterministic(big_bank):
    assert pick_question_ids(big_bank, "ivanov") == pick_question_ids(big_bank, "ivanov")
