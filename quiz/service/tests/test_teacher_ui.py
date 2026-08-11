"""Кнопки на страницах преподавателя.

Это обычные HTML-формы: страница должна работать с телефона и без JavaScript,
а после действия возвращать на ту же страницу, чтобы обновление браузера
не повторяло действие.
"""

from __future__ import annotations

from test_flow import issue, login, make_quiz, questions_on_page


def test_index_offers_a_create_form_with_the_available_lectures(teacher):
    page = teacher.get("/teacher").text
    assert 'action="/teacher/quizzes"' in page
    assert 'value="10-encoding"' in page
    assert "Пробный прогон" in page and "Боевой режим" in page


def test_create_button_makes_a_quiz_and_lands_on_it(teacher):
    resp = teacher.post(
        "/teacher/quizzes",
        data={"lecture": "10-encoding", "mode": "practice", "timeout_sec": 120},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/teacher/quizzes/1"
    assert "Управление" in teacher.get("/teacher/quizzes/1").text


def test_create_for_an_unknown_lecture_says_so_instead_of_crashing(teacher):
    resp = teacher.post(
        "/teacher/quizzes", data={"lecture": "99-nope", "mode": "practice"}, follow_redirects=True
    )
    assert resp.status_code == 200
    assert "нет банка для лекции 99-nope" in resp.text


def test_open_and_close_buttons_toggle_the_state(teacher):
    quiz = make_quiz(teacher)
    teacher.post(f"/teacher/quizzes/{quiz['id']}/state", data={"state": "closed"})
    page = teacher.get(f"/teacher/quizzes/{quiz['id']}").text
    assert "закрыта" in page
    assert "Открыть приём" in page

    teacher.post(f"/teacher/quizzes/{quiz['id']}/state", data={"state": "open"})
    page = teacher.get(f"/teacher/quizzes/{quiz['id']}").text
    assert "Закрыть приём" in page


def test_mode_button_switches_to_graded_and_back(teacher):
    quiz = make_quiz(teacher, mode="practice")
    teacher.post(f"/teacher/quizzes/{quiz['id']}/mode", data={"mode": "graded", "timeout_sec": 90})
    page = teacher.get(f"/teacher/quizzes/{quiz['id']}").text
    assert "боевой режим, таймер 90 с" in page

    teacher.post(f"/teacher/quizzes/{quiz['id']}/mode", data={"mode": "practice", "timeout_sec": 90})
    assert "пробный прогон" in teacher.get(f"/teacher/quizzes/{quiz['id']}").text


def test_ticket_button_issues_and_lists_clickable_codes(teacher):
    quiz = make_quiz(teacher)
    resp = teacher.post(
        f"/teacher/quizzes/{quiz['id']}/tickets", data={"count": 4}, follow_redirects=True
    )
    assert "Выпущено билетов: 4" in resp.text
    page = teacher.get(f"/teacher/quizzes/{quiz['id']}").text
    assert "Свободные билеты (4)" in page
    assert page.count('<a href="/t/') >= 4


def test_absurd_ticket_count_is_refused_with_a_message(teacher):
    quiz = make_quiz(teacher)
    resp = teacher.post(
        f"/teacher/quizzes/{quiz['id']}/tickets", data={"count": 9000}, follow_redirects=True
    )
    assert "билетов бывает от 1 до 500" in resp.text


def test_used_ticket_leaves_the_free_list(client, teacher):
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 2)[0]
    login(client, token)
    page = teacher.get(f"/teacher/quizzes/{quiz['id']}").text
    assert "Свободные билеты (1)" in page


def test_buttons_need_the_teacher_token(client, teacher):
    quiz = make_quiz(teacher)
    client.cookies.clear()
    assert client.post("/teacher/quizzes", data={"lecture": "10-encoding"}).status_code == 403
    assert client.post(f"/teacher/quizzes/{quiz['id']}/state", data={"state": "open"}).status_code == 403
    assert client.post(f"/teacher/quizzes/{quiz['id']}/tickets", data={"count": 1}).status_code == 403
