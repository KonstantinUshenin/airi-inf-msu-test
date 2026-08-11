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
