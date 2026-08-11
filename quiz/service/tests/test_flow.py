"""Сквозной путь по HTTP: билет → вход → ответы → сдача → разбор,
и преподавательский контур поверх того же состояния.
"""

from __future__ import annotations

import re

import pytest

LOGIN = "Иванов Иван"


def make_quiz(teacher, *, mode="practice", timeout=120):
    resp = teacher.post(
        "/api/teacher/quizzes",
        json={"lecture": "10-encoding", "mode": mode, "timeout_sec": timeout},
    )
    assert resp.status_code == 200, resp.text
    quiz = resp.json()
    teacher.post(f"/api/teacher/quizzes/{quiz['id']}/state", json={"state": "open"})
    return quiz


def issue(teacher, quiz_id, count=3):
    resp = teacher.post(f"/api/teacher/quizzes/{quiz_id}/tickets", json={"count": count})
    assert resp.status_code == 200, resp.text
    return [t.replace("-", "") for t in resp.json()["tokens"]]


def login(client, token, name=LOGIN):
    """Тестовый вход. Статус не проверяем: отказ (закрытая пятиминутка,
    погашенный билет) — такой же законный исход, как и попадание на квиз."""
    return client.post(f"/t/{token}/test-login", data={"full_name": name}, follow_redirects=True)


def attempt_id_of(client, token):
    resp = client.get(f"/t/{token}", follow_redirects=False)
    assert resp.status_code == 303, resp.text
    return int(re.search(r"/quiz/(\d+)", resp.headers["location"]).group(1))


def questions_on_page(html):
    return re.findall(r'data-question="([^"]+)"', html)


# --- вход ----------------------------------------------------------------


def test_unknown_ticket_is_refused(client):
    resp = client.get("/t/ZZZZZZZZ")
    assert resp.status_code == 404
    assert "не существует" in resp.text


def test_closed_quiz_does_not_let_anyone_in(client, teacher):
    quiz = make_quiz(teacher)
    teacher.post(f"/api/teacher/quizzes/{quiz['id']}/state", json={"state": "closed"})
    token = issue(teacher, quiz["id"], 1)[0]

    resp = login(client, token)
    assert resp.status_code == 403
    assert "закрыта" in resp.text


def test_login_creates_attempt_and_burns_the_ticket(client, teacher):
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 2)[0]

    resp = login(client, token)
    assert LOGIN in resp.text
    assert len(questions_on_page(resp.text)) == 5

    tickets = teacher.get(f"/teacher/quizzes/{quiz['id']}").text
    assert "Билетов выпущено 2, из них не использовано 1" in tickets


def test_page_never_leaks_the_correct_answer(client, teacher):
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 1)[0]
    html = login(client, token).text
    # В шаблоне прохождения нет ни признака верности, ни эталона.
    assert "is_correct" not in html
    assert "Эталон" not in html
    assert "эталонный ответ" not in html.lower()


def test_answer_response_does_not_reveal_correctness(client, teacher):
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 1)[0]
    login(client, token)
    attempt = attempt_id_of(client, token)
    qid = questions_on_page(client.get(f"/quiz/{attempt}").text)[0]

    resp = client.post(f"/api/attempt/{attempt}/answer", json={"question_id": qid, "choice": 0})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_reload_keeps_the_same_questions(client, teacher):
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 1)[0]
    first = questions_on_page(login(client, token).text)
    attempt = attempt_id_of(client, token)
    second = questions_on_page(client.get(f"/quiz/{attempt}").text)
    assert first == second


def test_second_ticket_resumes_instead_of_restarting(client, teacher):
    quiz = make_quiz(teacher)
    one, two = issue(teacher, quiz["id"], 2)
    login(client, one)
    first = attempt_id_of(client, one)
    assert attempt_id_of(client, two) == first


def test_someone_elses_attempt_is_not_readable(client, teacher):
    quiz = make_quiz(teacher)
    one, two = issue(teacher, quiz["id"], 2)
    login(client, one)
    mine = attempt_id_of(client, one)

    client.cookies.clear()
    login(client, two, name="Петров Пётр")
    assert client.get(f"/quiz/{mine}").status_code == 403


# --- прохождение и разбор ------------------------------------------------


def test_full_pass_and_feedback(client, teacher):
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 1)[0]
    login(client, token)
    attempt = attempt_id_of(client, token)
    qids = questions_on_page(client.get(f"/quiz/{attempt}").text)

    for qid in qids:
        if qid.startswith("q-mc-"):
            client.post(f"/api/attempt/{attempt}/answer", json={"question_id": qid, "choice": 0})
        else:
            client.post(f"/api/attempt/{attempt}/answer", json={"question_id": qid, "text": "мой ответ"})

    resp = client.post(f"/api/attempt/{attempt}/submit")
    assert resp.json()["next"] == f"/result/{attempt}"

    page = client.get(f"/result/{attempt}").text
    assert "Готово" in page
    # Разбор по вариантам показывает верный ответ; открытый ждёт судью.
    assert "Верный ответ" in page or "Верно:" in page
    assert "Проверяется" in page


def test_practice_run_hides_the_score(client, teacher):
    quiz = make_quiz(teacher, mode="practice")
    token = issue(teacher, quiz["id"], 1)[0]
    login(client, token)
    attempt = attempt_id_of(client, token)
    client.post(f"/api/attempt/{attempt}/submit")

    page = client.get(f"/result/{attempt}").text
    assert "оценка не выставляется" in page
    assert "верных:" not in page


def test_practice_run_has_no_timer(client, teacher):
    quiz = make_quiz(teacher, mode="practice")
    token = issue(teacher, quiz["id"], 1)[0]
    assert "Без таймера" in login(client, token).text


def test_graded_run_has_a_server_side_deadline(client, teacher):
    quiz = make_quiz(teacher, mode="graded", timeout=120)
    token = issue(teacher, quiz["id"], 1)[0]
    html = login(client, token).text
    left = int(re.search(r'data-left="(\d+)"', html).group(1))
    assert 110 <= left <= 120


def test_after_the_deadline_answers_are_refused(client, teacher, settings):
    from quizapp.store import Store

    quiz = make_quiz(teacher, mode="graded", timeout=120)
    token = issue(teacher, quiz["id"], 1)[0]
    login(client, token)
    attempt = attempt_id_of(client, token)
    qid = questions_on_page(client.get(f"/quiz/{attempt}").text)[0]

    # Сдвигаем дедлайн в прошлое — время живёт на сервере, клиент на него не влияет.
    db = Store(settings.db_path)
    with db._lock:
        db._db.execute("UPDATE attempt SET deadline_at = started_at - 1 WHERE id = ?", (attempt,))
        db._db.commit()
    db.close()

    resp = client.post(f"/api/attempt/{attempt}/answer", json={"question_id": qid, "choice": 0})
    assert resp.status_code == 409
    assert client.get(f"/quiz/{attempt}", follow_redirects=False).status_code == 303


def test_submitting_twice_keeps_the_first_time(client, teacher, settings):
    from quizapp.store import Store

    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 1)[0]
    login(client, token)
    attempt = attempt_id_of(client, token)

    client.post(f"/api/attempt/{attempt}/submit")
    db = Store(settings.db_path)
    first = db.get_attempt(attempt).submitted_at
    client.post(f"/api/attempt/{attempt}/submit")
    assert db.get_attempt(attempt).submitted_at == first
    db.close()


# --- преподавательский контур --------------------------------------------


def test_teacher_endpoints_need_the_token(client, teacher):
    quiz = make_quiz(teacher)
    client.cookies.clear()
    assert client.post("/api/teacher/quizzes", json={"lecture": "10-encoding"}).status_code == 403
    assert client.get(f"/teacher/quizzes/{quiz['id']}").status_code == 403
    assert client.get(f"/api/teacher/quizzes/{quiz['id']}/tickets.pdf").status_code == 403


def test_teacher_token_works_as_a_header(client, teacher, settings):
    quiz = make_quiz(teacher)
    client.cookies.clear()
    resp = client.post(
        f"/api/teacher/quizzes/{quiz['id']}/tickets",
        json={"count": 2},
        headers={"X-Quiz-Token": settings.teacher_token},
    )
    assert resp.status_code == 200


def test_quiz_for_a_missing_bank_is_refused(teacher):
    resp = teacher.post("/api/teacher/quizzes", json={"lecture": "99-nope"})
    assert resp.status_code == 400
    assert "нет банка" in resp.json()["detail"]


def test_tickets_pdf_is_a_pdf(teacher):
    quiz = make_quiz(teacher)
    issue(teacher, quiz["id"], 4)
    resp = teacher.get(f"/api/teacher/quizzes/{quiz['id']}/tickets.pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


def test_teacher_sees_attempt_search_and_detail(client, teacher):
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 1)[0]
    login(client, token)
    attempt = attempt_id_of(client, token)
    qid = questions_on_page(client.get(f"/quiz/{attempt}").text)[0]
    client.post(f"/api/attempt/{attempt}/answer", json={"question_id": qid, "choice": 0})
    client.post(f"/api/attempt/{attempt}/submit")

    page = teacher.get(f"/teacher/quizzes/{quiz['id']}?q=иванов").text
    assert LOGIN in page
    assert "Сводка по вопросам банка" in page

    empty = teacher.get(f"/teacher/quizzes/{quiz['id']}?q=сидоров").text
    assert "Ничего не найдено" in empty

    detail = teacher.get(f"/teacher/attempts/{attempt}").text
    assert LOGIN in detail
    assert "от входа" in detail


def test_test_attempts_are_marked_as_such(client, teacher):
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 1)[0]
    login(client, token)
    assert "тест" in teacher.get(f"/teacher/quizzes/{quiz['id']}").text


def test_csv_export_has_a_row_per_answer(client, teacher):
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 1)[0]
    login(client, token)
    attempt = attempt_id_of(client, token)
    client.post(f"/api/attempt/{attempt}/submit")

    resp = teacher.get(f"/teacher/quizzes/{quiz['id']}/export.csv")
    assert resp.status_code == 200
    lines = [line for line in resp.text.splitlines() if line.strip()]
    assert lines[0].startswith("attempt_id,full_name,login,ticket")
    assert len(lines) == 6  # шапка и пять вопросов набора


def test_healthz_lists_banks(client):
    body = client.get("/healthz").json()
    assert body["ok"] is True
    assert body["banks"] == ["10-encoding"]
    assert body["auth"] == "test"


def test_broken_body_is_a_bad_request_not_a_crash(client, teacher):
    """Оборванный запрос с телефона не должен выглядеть как падение сервиса."""
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 1)[0]
    login(client, token)
    attempt = attempt_id_of(client, token)

    broken = client.post(
        f"/api/attempt/{attempt}/answer",
        content=b'{"question_id": "q-mc-000", "choi',
        headers={"Content-Type": "application/json"},
    )
    assert broken.status_code == 400

    not_an_object = client.post(f"/api/attempt/{attempt}/answer", json=[1, 2, 3])
    assert not_an_object.status_code == 400


def test_unknown_question_id_is_a_bad_request(client, teacher):
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 1)[0]
    login(client, token)
    attempt = attempt_id_of(client, token)

    resp = client.post(
        f"/api/attempt/{attempt}/answer", json={"question_id": "q-mc-нет-такого", "choice": 0}
    )
    assert resp.status_code == 400
    assert "неизвестный вопрос" in resp.json()["detail"]


def test_out_of_range_choice_is_refused(client, teacher):
    quiz = make_quiz(teacher)
    token = issue(teacher, quiz["id"], 1)[0]
    login(client, token)
    attempt = attempt_id_of(client, token)
    qid = [q for q in questions_on_page(client.get(f"/quiz/{attempt}").text) if q.startswith("q-mc-")][0]

    for bad in (-1, 99, "первый", None):
        resp = client.post(f"/api/attempt/{attempt}/answer", json={"question_id": qid, "choice": bad})
        assert resp.status_code == 400, bad


def test_service_starts_and_reports_a_broken_bank(settings, banks_dir, monkeypatch):
    """Битый банк раньше не давал стартовать всему сервису."""
    from fastapi.testclient import TestClient

    from conftest import make_bank_text
    from quizapp.config import Settings
    from quizapp.web import create_app

    broken = make_bank_text(lecture="11-hierarchy").replace("- [x] вариант A-0", "- [ ] вариант A-0", 1)
    (banks_dir / "11-hierarchy.md").write_text(broken, encoding="utf-8")

    with TestClient(create_app(Settings())) as client:
        body = client.get("/healthz").json()
        assert body["ok"] is True
        assert body["banks"] == ["10-encoding"]          # целый банк работает
        assert "11-hierarchy.md" in body["broken_banks"]  # поломка не замолчана

        client.cookies.set("quiz_teacher", "secret-teacher-token")
        page = client.get("/teacher").text
        assert "Не разобрано банков: 1" in page
        # По битой лекции пятиминутку завести нельзя — её просто нет в списке.
        assert 'value="11-hierarchy"' not in page
