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
    picked = _spread_by_slide(bank, mc_ids, n_mc, rnd)
    picked += rnd.sample(open_ids, n_open)
    return picked


def _spread_by_slide(bank: Bank, ids: list[str], count: int, rnd: random.Random) -> list[str]:
    """Выбрать `count` вопросов, стараясь не брать два с одного слайда.

    Без этого набор из пяти вопросов легко вырождается: в банке по восемь
    вопросов на раздел, и честно случайная выборка регулярно выдаёт студенту
    два вопроса про одно и то же, а половину лекции не трогает вовсе.

    Если разных слайдов меньше, чем нужно вопросов, ограничение отпускается —
    маленький банк лучше, чем отказ выдать набор.
    """
    by_slide: dict[str, list[str]] = {}
    for qid in ids:
        by_slide.setdefault(bank.by_id[qid].slide, []).append(qid)

    slides = sorted(by_slide)
    rnd.shuffle(slides)

    picked: list[str] = []
    for slide in slides:
        if len(picked) == count:
            break
        picked.append(rnd.choice(sorted(by_slide[slide])))

    if len(picked) < count:
        rest = sorted(set(ids) - set(picked))
        picked += rnd.sample(rest, count - len(picked))

    rnd.shuffle(picked)
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
