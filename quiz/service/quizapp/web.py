"""HTTP-слой: студенческий вход, прохождение, преподавательский контур.

Два правила, которые здесь важнее всех остальных:

1. Правильность считается только тут, на сервере. В шаблон прохождения не
   уезжает ни признак верности, ни эталон — до момента сдачи.
2. Время тоже живёт тут. Клиент рисует обратный отсчёт от серверного дедлайна,
   но ни одна отметка времени с клиента не принимается и не хранится.
"""

from __future__ import annotations

import csv
import io
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .auth import SESSION_COOKIE, STATE_COOKIE, AuthError, Identity, OidcClient, Sessions, test_identity
from .bank import Bank, scan_banks
from .config import Settings, checkout_revision
from .judge import Judge
from .selection import pick_question_ids, shown_options
from .store import Attempt, Store, normalize_token, pretty_token

HERE = Path(__file__).parent
TEACHER_COOKIE = "quiz_teacher"
log = logging.getLogger("quizapp.web")


def create_app(settings: Settings | None = None, *, store: Store | None = None) -> FastAPI:
    s = settings or Settings()
    # Непригодный банк не мешает остальным: он просто не попадает в список,
    # а его поломка едет в лог, в /healthz и на страницу преподавателя.
    banks: dict[str, Bank] = {}
    bank_errors: dict[str, str] = {}
    if s.banks_dir.exists():
        banks, bank_errors = scan_banks(s.banks_dir)
    for name, problem in bank_errors.items():
        log.error("банк %s не разобран и пропущен: %s", name, problem)
    db = store or Store(s.db_path)
    if s.auto_provision and banks:
        for lecture in provision_from_banks(db, banks, ticket_count=s.auto_tickets):
            log.info("лекция %s: заведена пятиминутка и %d билетов", lecture, s.auto_tickets)
    sessions = Sessions(s.secret_key)
    oidc = OidcClient(s) if s.auth_mode == "oidc" else None
    judge = Judge(s, db, banks)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        judge.start()
        yield
        await judge.stop()

    app = FastAPI(title="Пятиминутки", lifespan=lifespan)
    app.state.settings = s
    app.state.store = db
    app.state.banks = banks
    app.state.bank_errors = bank_errors
    app.state.judge = judge

    templates = Jinja2Templates(directory=str(HERE / "templates"))
    templates.env.filters["mmss"] = _mmss
    templates.env.filters["clock"] = _clock
    app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")

    # --- вспомогательное --------------------------------------------------

    def bank_for(lecture: str) -> Bank:
        bank = banks.get(lecture)
        if bank is None:
            raise HTTPException(500, f"нет банка вопросов для лекции {lecture}")
        return bank

    def page(name: str, request: Request, **ctx) -> HTMLResponse:
        status = int(ctx.pop("status", 200))
        return templates.TemplateResponse(
            request, name, {"settings": s, **ctx}, status_code=status
        )

    def require_teacher(request: Request) -> None:
        if not s.teacher_token:
            raise HTTPException(503, "QUIZ_TEACHER_TOKEN не задан — преподавательский контур выключен")
        supplied = request.headers.get("X-Quiz-Token") or request.cookies.get(TEACHER_COOKIE) or ""
        if not _same(supplied, s.teacher_token):
            raise HTTPException(403, "нужен преподавательский токен")

    def live_attempt(attempt_id: int, request: Request) -> Attempt:
        attempt = db.get_attempt(attempt_id)
        if attempt is None:
            raise HTTPException(404, "попытки нет")
        identity = sessions.load(request.cookies.get(SESSION_COOKIE))
        if identity is None or identity.login != attempt.login:
            raise HTTPException(403, "это чужая попытка")
        return attempt

    def autosubmit_if_expired(attempt: Attempt, now: float) -> Attempt:
        if not attempt.submitted and attempt.expired(now):
            db.submit(attempt.id, now=attempt.deadline_at or now)
            _enqueue_open(db, attempt.id)
            return db.get_attempt(attempt.id)  # type: ignore[return-value]
        return attempt

    # --- вход по билету ---------------------------------------------------

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return page("index.html", request)

    @app.get("/t/{token}", response_class=HTMLResponse)
    async def enter(token: str, request: Request):
        token = normalize_token(token)
        ticket = db.get_ticket(token)
        if ticket is None:
            return page("denied.html", request, reason="Такого билета не существует.", status=404)

        quiz = db.get_quiz(ticket["quiz_id"])
        identity = sessions.load(request.cookies.get(SESSION_COOKIE))
        if identity is None:
            if s.auth_mode == "test":
                return page("login_test.html", request, token=token, quiz=quiz)
            assert oidc is not None
            state = oidc.new_state()
            url = await oidc.authorize_url(state=state, redirect_uri=_redirect_uri(s))
            resp = RedirectResponse(url, status_code=303)
            resp.set_cookie(
                STATE_COOKIE,
                sessions.dump(Identity(login=state, full_name=token, is_test=False)),
                httponly=True,
                samesite="lax",
                max_age=900,
            )
            return resp

        return _start_or_resume(request, db, s, banks, ticket, quiz, identity, page)

    @app.post("/t/{token}/test-login")
    async def test_login(token: str, request: Request, full_name: str = Form(...)):
        if s.auth_mode != "test":
            raise HTTPException(404, "тестовый вход выключен")
        try:
            identity = test_identity(full_name)
        except AuthError as exc:
            quiz = db.get_quiz(db.get_ticket(normalize_token(token))["quiz_id"])  # type: ignore[index]
            return page("login_test.html", request, token=token, quiz=quiz, error=str(exc))
        resp = RedirectResponse(f"/t/{normalize_token(token)}", status_code=303)
        resp.set_cookie(SESSION_COOKIE, sessions.dump(identity), httponly=True, samesite="lax")
        return resp

    @app.get("/auth/callback")
    async def callback(request: Request, code: str = "", state: str = ""):
        if oidc is None:
            raise HTTPException(404, "OIDC выключен")
        saved = sessions.load(request.cookies.get(STATE_COOKIE))
        if saved is None or saved.login != state:
            return page("denied.html", request, reason="Вход не подтвердился, попробуйте ещё раз.", status=400)
        try:
            identity = await oidc.exchange(code=code, redirect_uri=_redirect_uri(s))
        except AuthError as exc:
            return page("denied.html", request, reason=str(exc), status=502)
        resp = RedirectResponse(f"/t/{saved.full_name}", status_code=303)
        resp.set_cookie(SESSION_COOKIE, sessions.dump(identity), httponly=True, samesite="lax")
        resp.delete_cookie(STATE_COOKIE)
        return resp

    # --- прохождение ------------------------------------------------------

    @app.get("/quiz/{attempt_id}", response_class=HTMLResponse)
    async def take(attempt_id: int, request: Request):
        now = time.time()
        attempt = autosubmit_if_expired(live_attempt(attempt_id, request), now)
        if attempt.submitted:
            return RedirectResponse(f"/result/{attempt.id}", status_code=303)

        quiz = db.get_quiz(attempt.quiz_id)
        bank = bank_for(quiz.lecture)
        rows = db.answers_for(attempt.id)
        items = []
        for row in rows:
            q = bank.by_id[row["question_id"]]
            items.append(
                {
                    "id": q.id,
                    "kind": q.kind,
                    "prompt": q.prompt,
                    "options": shown_options(q, attempt.login) if q.kind == "mc" else [],
                    "choice": row["choice"],
                    "text": row["text"] or "",
                }
            )
        left = int(attempt.deadline_at - now) if attempt.deadline_at else None
        return page("take.html", request, attempt=attempt, quiz=quiz, items=items, seconds_left=left)

    @app.post("/api/attempt/{attempt_id}/answer")
    async def answer(attempt_id: int, request: Request):
        now = time.time()
        attempt = live_attempt(attempt_id, request)
        if attempt.submitted:
            raise HTTPException(409, "попытка уже сдана")
        if attempt.expired(now):
            autosubmit_if_expired(attempt, now)
            raise HTTPException(409, "время вышло")

        body = await _json_object(request)
        question_id = str(body.get("question_id", ""))
        quiz = db.get_quiz(attempt.quiz_id)
        bank = bank_for(quiz.lecture)
        question = bank.by_id.get(question_id)
        if question is None:
            raise HTTPException(400, "неизвестный вопрос")

        if question.kind == "mc":
            choice = body.get("choice")
            if not isinstance(choice, int) or not 0 <= choice < len(question.options):
                raise HTTPException(400, "неверный номер варианта")
            db.record_answer(
                attempt.id,
                question_id,
                choice=choice,
                is_correct=choice == question.correct_index,
                now=now,
            )
        else:
            db.record_answer(attempt.id, question_id, text=str(body.get("text", ""))[:4000], now=now)
        # В ответе намеренно нет ни признака верности, ни правильного варианта.
        return {"ok": True}

    @app.post("/api/attempt/{attempt_id}/submit")
    async def submit(attempt_id: int, request: Request):
        now = time.time()
        attempt = live_attempt(attempt_id, request)
        if not attempt.submitted:
            db.submit(attempt.id, now=now)
            _enqueue_open(db, attempt.id)
        return {"ok": True, "next": f"/result/{attempt.id}"}

    @app.get("/result/{attempt_id}", response_class=HTMLResponse)
    async def result(attempt_id: int, request: Request):
        now = time.time()
        attempt = autosubmit_if_expired(live_attempt(attempt_id, request), now)
        if not attempt.submitted:
            return RedirectResponse(f"/quiz/{attempt.id}", status_code=303)

        quiz = db.get_quiz(attempt.quiz_id)
        bank = bank_for(quiz.lecture)
        verdicts = db.judgements_for(attempt.id)
        items, correct = [], 0
        for row in db.answers_for(attempt.id):
            q = bank.by_id[row["question_id"]]
            item = {
                "kind": q.kind,
                "prompt": q.prompt,
                "slide": q.slide,
                "answered": row["answered_at"] is not None,
                "is_correct": None if row["is_correct"] is None else bool(row["is_correct"]),
            }
            if q.kind == "mc":
                item["chosen"] = q.options[row["choice"]].text if row["choice"] is not None else None
                item["correct_option"] = q.options[q.correct_index].text
            else:
                item["text"] = row["text"] or ""
                item["reference"] = q.reference
                judgement = verdicts.get(row["id"])
                item["status"] = judgement["status"] if judgement else "queued"
                item["rationale"] = judgement["rationale"] if judgement else ""
            if row["is_correct"] == 1:
                correct += 1
            items.append(item)

        return page(
            "result.html",
            request,
            attempt=attempt,
            quiz=quiz,
            items=items,
            correct=correct,
            total=len(items),
            duration=(attempt.submitted_at or now) - attempt.started_at,
        )

    @app.get("/api/attempt/{attempt_id}/verdict")
    async def verdict(attempt_id: int, request: Request):
        """Опрос вердикта: страница разбора обновляет открытый вопрос сама."""
        attempt = live_attempt(attempt_id, request)
        verdicts = db.judgements_for(attempt.id)
        out = []
        for row in db.answers_for(attempt.id):
            if row["kind"] != "open":
                continue
            j = verdicts.get(row["id"])
            out.append(
                {
                    "question_id": row["question_id"],
                    "status": j["status"] if j else "queued",
                    "is_correct": None if not j or j["is_correct"] is None else bool(j["is_correct"]),
                    "rationale": j["rationale"] if j else "",
                }
            )
        return {"items": out}

    # --- преподавательский контур ----------------------------------------

    @app.get("/teacher", response_class=HTMLResponse)
    async def teacher_home(request: Request, error: str = "", note: str = ""):
        supplied = request.cookies.get(TEACHER_COOKIE) or ""
        if not s.teacher_token or not _same(supplied, s.teacher_token):
            return page("teacher_login.html", request)
        # Страница строится от лекций, а не от пятиминуток: пятиминутка теперь
        # ровно одна на лекцию и заводится сама, так что «список лекций» и есть
        # список пятиминуток.
        quizzes = {q.lecture: q for q in db.list_quizzes()}
        rows = [
            {"lecture": slug, "bank": banks[slug], "quiz": quizzes.get(slug)}
            for slug in sorted(banks)
        ]
        orphans = [q for lecture, q in sorted(quizzes.items()) if lecture not in banks]
        return page(
            "teacher_index.html",
            request,
            rows=rows,
            orphans=orphans,
            bank_errors=bank_errors,
            auto=s.auto_provision,
            error=error,
            note=note,
        )

    # --- кнопки на страницах преподавателя --------------------------------
    #
    # Обычные HTML-формы, а не JSON: страница должна работать с телефона
    # и без JavaScript, а после действия — возвращать на ту же страницу
    # (post/redirect/get), чтобы обновление браузера не повторяло действие.
    # JSON-ручки рядом никуда не делись: их зовут CLI и скрипты.

    @app.post("/teacher/quizzes", dependencies=[Depends(require_teacher)])
    async def teacher_create(lecture: str = Form(...)):
        """Завести пятиминутку по лекции, у которой её почему-то нет.

        Обычно этого не требуется: пятиминутки заводятся сами при появлении
        банка. Кнопка остаётся на случай выключенного автозаведения. Настройки
        здесь не спрашиваются — их правят на странице самой пятиминутки.
        """
        if lecture not in banks:
            return _back("/teacher", error=f"нет банка для лекции {lecture}")
        existing = db.quiz_for_lecture(lecture)
        if existing is not None:
            return _back(f"/teacher/quizzes/{existing.id}",
                         note="По этой лекции пятиминутка уже была")
        quiz = db.create_quiz(lecture, banks[lecture].title)
        db.issue_tickets(quiz.id, s.auto_tickets)
        return RedirectResponse(f"/teacher/quizzes/{quiz.id}", status_code=303)

    @app.post("/teacher/quizzes/{quiz_id}/state", dependencies=[Depends(require_teacher)])
    async def teacher_state(quiz_id: int, state: str = Form(...)):
        db.update_quiz(quiz_id, state=state)
        return _back(f"/teacher/quizzes/{quiz_id}",
                     note="Пятиминутка открыта" if state == "open" else "Пятиминутка закрыта")

    @app.post("/teacher/quizzes/{quiz_id}/mode", dependencies=[Depends(require_teacher)])
    async def teacher_mode(quiz_id: int, mode: str = Form(...), timeout_sec: int = Form(0)):
        db.update_quiz(quiz_id, mode=mode, timeout_sec=timeout_sec or s.default_timeout_sec,
                       touch_timeout=True)
        return _back(f"/teacher/quizzes/{quiz_id}",
                     note="Боевой режим: таймер и оценки" if mode == "graded"
                          else "Пробный режим: без таймера и без оценок")

    @app.post("/teacher/quizzes/{quiz_id}/tickets", dependencies=[Depends(require_teacher)])
    async def teacher_tickets(quiz_id: int, count: int = Form(36)):
        if not 1 <= count <= 500:
            return _back(f"/teacher/quizzes/{quiz_id}", error="билетов бывает от 1 до 500")
        tokens = db.issue_tickets(quiz_id, count)
        return _back(f"/teacher/quizzes/{quiz_id}", note=f"Выпущено билетов: {len(tokens)}")

    @app.post("/teacher/login")
    async def teacher_login(request: Request, token: str = Form(...)):
        if not s.teacher_token or not _same(token, s.teacher_token):
            return page("teacher_login.html", request, error="Токен не подошёл.")
        resp = RedirectResponse("/teacher", status_code=303)
        resp.set_cookie(TEACHER_COOKIE, token, httponly=True, samesite="lax")
        return resp

    @app.post("/api/teacher/quizzes", dependencies=[Depends(require_teacher)])
    async def create_quiz(request: Request):
        """Идемпотентно: по лекции может существовать ровно одна пятиминутка.

        Повторный вызов возвращает уже существующую, а не заводит вторую и не
        падает: скрипту так проще, а «одна лекция — одна пятиминутка» держит
        уникальный индекс в базе.
        """
        body = await _json_object(request)
        lecture = str(body.get("lecture", "")).strip()
        if lecture not in banks:
            raise HTTPException(400, f"нет банка для лекции {lecture!r}; есть: {sorted(banks)}")

        quiz = db.quiz_for_lecture(lecture)
        if quiz is None:
            quiz = db.create_quiz(
                lecture,
                str(body.get("title") or banks[lecture].title),
                mode=str(body.get("mode", "practice")),
                timeout_sec=body.get("timeout_sec") or s.default_timeout_sec,
            )
            db.issue_tickets(quiz.id, s.auto_tickets)
        return _quiz_json(quiz)

    @app.post("/api/teacher/quizzes/{quiz_id}/state", dependencies=[Depends(require_teacher)])
    async def set_state(quiz_id: int, request: Request):
        body = await _json_object(request)
        quiz = db.update_quiz(
            quiz_id,
            state=body.get("state"),
            mode=body.get("mode"),
            timeout_sec=body.get("timeout_sec"),
            touch_timeout="timeout_sec" in body,
        )
        return _quiz_json(quiz)

    @app.post("/api/teacher/quizzes/{quiz_id}/tickets", dependencies=[Depends(require_teacher)])
    async def make_tickets(quiz_id: int, request: Request):
        body = await _json_object(request) if await request.body() else {}
        try:
            count = int(body.get("count", 36))
        except (TypeError, ValueError):
            raise HTTPException(400, "count — целое число") from None
        if not 1 <= count <= 500:
            raise HTTPException(400, "разумное число билетов — от 1 до 500")
        tokens = db.issue_tickets(quiz_id, count)
        return {"tokens": [pretty_token(t) for t in tokens], "count": len(tokens)}

    @app.get("/api/teacher/quizzes/{quiz_id}/tickets.pdf", dependencies=[Depends(require_teacher)])
    async def tickets_pdf(quiz_id: int, only_fresh: bool = True):
        from .tickets import build_pdf  # локально: reportlab тяжело импортируется

        quiz = db.get_quiz(quiz_id)
        rows = db.tickets_for(quiz_id)
        tokens = [r["token"] for r in rows if not (only_fresh and r["redeemed_at"])]
        if not tokens:
            raise HTTPException(404, "нечего печатать: билеты не выпущены или уже погашены")
        pdf = build_pdf(
            base_url=s.base_url,
            tokens=tokens,
            heading=f"Пятиминутка — {quiz.title or quiz.lecture} · билетов: {len(tokens)}",
        )
        return Response(
            pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="tickets-{quiz_id}.pdf"'},
        )

    @app.get("/teacher/quizzes/{quiz_id}", response_class=HTMLResponse, dependencies=[Depends(require_teacher)])
    async def teacher_quiz(quiz_id: int, request: Request, q: str = "", error: str = "", note: str = ""):
        quiz = db.get_quiz(quiz_id)
        bank = banks.get(quiz.lecture)
        summary = db.question_summary(quiz_id)
        for row in summary:
            question = bank.by_id.get(row["question_id"]) if bank else None
            row["prompt"] = question.prompt if question else "(вопроса нет в банке)"
        tickets = [
            {
                "token": r["token"],
                "pretty": pretty_token(r["token"]),
                "url": f"{s.base_url}/t/{r['token']}",
                "redeemed": r["redeemed_at"] is not None,
            }
            for r in db.tickets_for(quiz_id)
        ]
        return page(
            "teacher_quiz.html",
            request,
            quiz=quiz,
            bank=bank,
            attempts=db.attempts_table(quiz_id, q),
            summary=summary,
            durations=db.durations(quiz_id),
            failures=db.judge_failures(quiz_id),
            query=q,
            tickets=tickets,
            fresh=[t for t in tickets if not t["redeemed"]],
            error=error,
            note=note,
        )

    @app.get("/teacher/attempts/{attempt_id}", response_class=HTMLResponse, dependencies=[Depends(require_teacher)])
    async def teacher_attempt(attempt_id: int, request: Request):
        attempt = db.get_attempt(attempt_id)
        if attempt is None:
            raise HTTPException(404, "попытки нет")
        quiz = db.get_quiz(attempt.quiz_id)
        bank = banks.get(quiz.lecture)
        verdicts = db.judgements_for(attempt.id)
        rows = []
        previous = attempt.started_at
        for row in db.answers_for(attempt.id):
            question = bank.by_id.get(row["question_id"]) if bank else None
            answered = row["answered_at"]
            judgement = verdicts.get(row["id"])
            rows.append(
                {
                    "question_id": row["question_id"],
                    "prompt": question.prompt if question else "(вопроса нет в банке)",
                    "kind": row["kind"],
                    "chosen": (
                        question.options[row["choice"]].text
                        if question and row["kind"] == "mc" and row["choice"] is not None
                        else None
                    ),
                    "text": row["text"],
                    "is_correct": None if row["is_correct"] is None else bool(row["is_correct"]),
                    "changes": row["changes"],
                    "since_start": (answered - attempt.started_at) if answered else None,
                    "since_previous": (answered - previous) if answered else None,
                    "judge_status": judgement["status"] if judgement else None,
                    "rationale": judgement["rationale"] if judgement else "",
                }
            )
            if answered:
                previous = answered
        return page(
            "teacher_attempt.html",
            request,
            attempt=attempt,
            quiz=quiz,
            rows=rows,
            ticket=pretty_token(attempt.ticket_token),
        )

    @app.get("/teacher/quizzes/{quiz_id}/export.csv", dependencies=[Depends(require_teacher)])
    async def export_csv(quiz_id: int):
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            ["attempt_id", "full_name", "login", "ticket", "is_test", "question_id", "kind",
             "answer", "is_correct", "changes", "seconds_from_start", "started_at", "submitted_at"]
        )
        quiz = db.get_quiz(quiz_id)
        bank = banks.get(quiz.lecture)
        for meta in db.attempts_table(quiz_id):
            attempt = db.get_attempt(meta["id"])
            assert attempt is not None
            for row in db.answers_for(attempt.id):
                question = bank.by_id.get(row["question_id"]) if bank else None
                if row["kind"] == "mc":
                    value = (
                        question.options[row["choice"]].text
                        if question and row["choice"] is not None
                        else ""
                    )
                else:
                    value = row["text"] or ""
                writer.writerow(
                    [
                        attempt.id, attempt.full_name, attempt.login, pretty_token(attempt.ticket_token),
                        int(attempt.is_test), row["question_id"], row["kind"], value,
                        "" if row["is_correct"] is None else int(row["is_correct"]),
                        row["changes"],
                        "" if row["answered_at"] is None else round(row["answered_at"] - attempt.started_at, 2),
                        _clock(attempt.started_at),
                        _clock(attempt.submitted_at) if attempt.submitted_at else "",
                    ]
                )
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="quiz-{quiz_id}.csv"'},
        )

    @app.get("/healthz")
    async def healthz():
        # Непригодные банки видны здесь, а не только в логе: сервис жив, но
        # часть лекций недоступна, и это должно быть заметно снаружи.
        return JSONResponse(
            {
                "ok": True,
                "version": checkout_revision(),
                "banks": sorted(banks),
                "broken_banks": bank_errors,
                "auth": s.auth_mode,
                "judge": "on" if (s.judge_enabled and s.judge_configured) else "off",
                "judge_model": s.llm_model if s.judge_configured else None,
                "judge_endpoint": s.llm_base_url if s.judge_configured else None,
                "judge_queue": db.judge_queue_stats(),
            }
        )

    return app


# --- функции без замыканий (их проще тестировать) -------------------------


def _start_or_resume(request, db: Store, s: Settings, banks, ticket, quiz, identity: Identity, page):
    """Создать попытку по билету или вернуть уже существующую."""
    existing = db.attempt_by_login(quiz.id, identity.login)
    if existing is not None:
        return RedirectResponse(f"/quiz/{existing.id}", status_code=303)

    if not quiz.is_open:
        return page("denied.html", request, reason="Пятиминутка закрыта.", status=403)
    if ticket["redeemed_at"] is not None:
        return page(
            "denied.html",
            request,
            reason="Этот билет уже использован — возьмите другой.",
            status=409,
        )

    bank = banks.get(quiz.lecture)
    if bank is None:
        raise HTTPException(500, f"нет банка вопросов для лекции {quiz.lecture}")
    ids = pick_question_ids(bank, identity.login)
    questions = [(qid, bank.by_id[qid].kind) for qid in ids]
    attempt = db.redeem(
        ticket["token"],
        login=identity.login,
        full_name=identity.full_name,
        is_test=identity.is_test,
        questions=questions,
        timeout_sec=quiz.timeout_sec if quiz.graded else None,
    )
    return RedirectResponse(f"/quiz/{attempt.id}", status_code=303)


def provision_from_banks(
    db: Store, banks: dict[str, Bank], *, ticket_count: int
) -> list[str]:
    """Завести пятиминутку и билеты для каждой лекции, у которой их ещё нет.

    Появился в репозитории банк новой лекции — после деплоя всё уже готово:
    остаётся поправить настройки и открыть приём. Пятиминутка создаётся
    ЗАКРЫТОЙ и в пробном режиме: открыть должен человек, а не выкатка.

    Идемпотентно. Существующие пятиминутки не трогаются вовсе — ни настройки,
    ни билеты: преподаватель мог их менять, и перезапуск сервиса не имеет права
    это откатывать. Билеты досоздаются только если их нет совсем.
    """
    created: list[str] = []
    for lecture in sorted(banks):
        if db.quiz_for_lecture(lecture) is not None:
            continue
        quiz = db.create_quiz(lecture, banks[lecture].title)
        db.issue_tickets(quiz.id, ticket_count)
        created.append(lecture)
    return created


def _back(path: str, *, note: str = "", error: str = "") -> RedirectResponse:
    """Вернуться на страницу после действия, показав, что произошло."""
    params = urlencode({k: v for k, v in (("note", note), ("error", error)) if v})
    return RedirectResponse(f"{path}?{params}" if params else path, status_code=303)


async def _json_object(request: Request) -> dict:
    """Тело запроса как объект.

    Ответы летят с телефонов на аудиторном wifi, и оборванный запрос — это
    плохой запрос, а не падение сервиса: без этого битый JSON давал 500.
    """
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        raise HTTPException(400, "тело запроса не разобрано как JSON") from None
    if not isinstance(body, dict):
        raise HTTPException(400, "ожидается объект JSON")
    return body


def _enqueue_open(db: Store, attempt_id: int) -> None:
    for row in db.answers_for(attempt_id):
        if row["kind"] == "open" and row["answered_at"] is not None:
            db.enqueue_judgement(row["id"])


def _redirect_uri(s: Settings) -> str:
    return f"{s.base_url}/auth/callback"


def _same(a: str, b: str) -> bool:
    import hmac

    return hmac.compare_digest(a.strip(), b.strip())


def _quiz_json(quiz) -> dict:
    return {
        "id": quiz.id,
        "lecture": quiz.lecture,
        "title": quiz.title,
        "state": quiz.state,
        "mode": quiz.mode,
        "timeout_sec": quiz.timeout_sec,
    }


def _mmss(seconds) -> str:
    if seconds is None:
        return "—"
    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def _clock(epoch) -> str:
    if not epoch:
        return "—"
    return time.strftime("%d.%m %H:%M:%S", time.localtime(epoch))
