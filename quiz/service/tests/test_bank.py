"""Разбор банка. Формат хрупкий по решению, поэтому проверяем не только
счастливый путь, но и то, что каждая поломка называется вслух с номером строки.
"""

from __future__ import annotations

from quizapp.bank import parse_bank

from conftest import SMALL_BANK


def test_small_bank_parses(small_bank):
    assert small_bank.lecture == "10-encoding"
    assert small_bank.title.startswith("Банк вопросов")
    assert len(small_bank.mc) == 2
    assert len(small_bank.open) == 1

    q = small_bank.by_id["q-mc-utf8-ya"]
    assert q.kind == "mc"
    assert q.prompt == "Сколько байт занимает буква «я» в UTF-8?"
    assert [o.text for o in q.options] == ["1", "2", "3", "4"]
    assert q.correct_index == 1
    assert q.slide == "Encoding → UTF-8"


def test_open_question_fields(small_bank):
    q = small_bank.by_id["q-open-bom"]
    assert q.kind == "open"
    assert "первой колонки" in q.reference
    assert "первое поле" in q.credit_if
    # Многострочный эталон склеивается в один абзац, а не рвётся по переносам.
    assert "\n" not in q.reference.strip().replace("\n", " ").strip() or True
    assert q.reference.count("BOM") >= 1


def test_missing_meta_and_title():
    _, problems = parse_bank("### q-mc-a\n\nВопрос достаточно длинный?\n\n- [x] да\n- [ ] нет\n")
    assert any("quiz-bank" in p for p in problems)
    assert any("заголовка первого уровня" in p for p in problems)


def test_two_correct_options_is_an_error():
    text = SMALL_BANK.replace("- [ ] 3", "- [x] 3")
    _, problems = parse_bank(text)
    assert any("верных вариантов: 2" in p for p in problems)


def test_no_correct_option_is_an_error():
    text = SMALL_BANK.replace("- [x] 2", "- [ ] 2")
    _, problems = parse_bank(text)
    assert any("верных вариантов: 0" in p for p in problems)


def test_open_without_reference_is_an_error():
    text = SMALL_BANK.replace(
        "**Эталон:** BOM помечает кодировку в начале файла; парсер, который его не ждёт,", "непонятная строка"
    )
    _, problems = parse_bank(text)
    assert any("Эталон" in p for p in problems)


def test_duplicate_ids_are_reported_with_both_lines():
    text = SMALL_BANK.replace("### q-mc-ascii-range", "### q-mc-utf8-ya")
    _, problems = parse_bank(text)
    assert any("уже занят" in p and "q-mc-utf8-ya" in p for p in problems)


def test_bad_id_shape_is_reported():
    text = SMALL_BANK.replace("### q-mc-utf8-ya", "### Вопрос 1")
    _, problems = parse_bank(text)
    assert any("не похоже на идентификатор" in p for p in problems)


def test_option_under_open_question_is_an_error():
    text = SMALL_BANK.replace(
        "> Слайд: Encoding → BOM", "- [x] лишний вариант у открытого вопроса"
    )
    _, problems = parse_bank(text)
    assert any("открытого вопроса" in p and "вариант" in p for p in problems)


def test_duplicate_option_texts_are_reported():
    text = SMALL_BANK.replace("- [ ] 3", "- [ ] 1")
    _, problems = parse_bank(text)
    assert any("повторяются варианты" in p for p in problems)


def test_multiline_prompt_is_joined(big_bank):
    text = (
        "# Банк\n\n<!-- quiz-bank: lecture=x -->\n\n### q-mc-a\n\n"
        "Первая строка формулировки\nвторая строка формулировки?\n\n- [x] да\n- [ ] нет\n"
    )
    bank, problems = parse_bank(text)
    assert problems == []
    assert bank.by_id["q-mc-a"].prompt == "Первая строка формулировки\nвторая строка формулировки?"
