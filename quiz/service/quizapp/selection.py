"""Выборка набора вопросов и порядка вариантов.

Всё здесь — чистые функции от (лекция, логин) и от идентификатора вопроса.
Никакого состояния и никакого системного времени: набор обязан быть одинаковым
при перезагрузке страницы, при возврате после потери сети и при пересчёте
аналитики задним числом. По той же причине идентификаторы вопросов в банке
объявлены стабильными — переименование вопроса меняет и наборы, и сводку.
"""

from __future__ import annotations

import hashlib
import random

from .bank import Bank, Question

DEFAULT_MC = 4
DEFAULT_OPEN = 1


def _rng(*parts: str) -> random.Random:
    seed = hashlib.blake2b("\x1f".join(parts).encode("utf-8"), digest_size=16).digest()
    return random.Random(int.from_bytes(seed, "big"))


def pick_question_ids(
    bank: Bank, login: str, *, n_mc: int = DEFAULT_MC, n_open: int = DEFAULT_OPEN
) -> list[str]:
    """Идентификаторы вопросов набора: сначала с вариантами, в конце открытый."""
    mc_ids = sorted(q.id for q in bank.mc)
    open_ids = sorted(q.id for q in bank.open)

    if len(mc_ids) < n_mc:
        raise ValueError(
            f"в банке {bank.lecture} {len(mc_ids)} вопросов с вариантами, нужно {n_mc}"
        )
    if len(open_ids) < n_open:
        raise ValueError(
            f"в банке {bank.lecture} {len(open_ids)} открытых вопросов, нужно {n_open}"
        )

    rnd = _rng(bank.lecture, login)
    picked = rnd.sample(mc_ids, n_mc)
    picked += rnd.sample(open_ids, n_open)
    return picked


def option_order(question: Question) -> list[int]:
    """Порядок показа вариантов — перестановка исходных индексов.

    Зависит только от идентификатора вопроса: у соседей всё равно разные
    вопросы, а привязка к логину сделала бы невоспроизводимой сводку
    «какой вариант чаще выбирали».
    """
    order = list(range(len(question.options)))
    _rng("options", question.id).shuffle(order)
    return order


def shown_options(question: Question) -> list[tuple[int, str]]:
    """Пары (исходный индекс, текст) в порядке показа."""
    return [(i, question.options[i].text) for i in option_order(question)]
