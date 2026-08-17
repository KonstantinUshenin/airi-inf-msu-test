"""Хранилище: SQLite плюс тонкий слой запросов.

Соединение одно на процесс, доступ под замком. Для тридцати шести человек,
жмущих кнопки в течение двух минут, это заведомо достаточно, а взамен
не появляется ни пула, ни отдельного демона.

Ни один метод здесь не ходит в сеть и не знает про HTTP.
"""

from __future__ import annotations

import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")

# Без 0/O, 1/I/L и U: код диктуют вслух и переписывают с бумаги.
TOKEN_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"
TOKEN_LEN = 8

MAX_JUDGE_TRIES = 5


class StoreError(Exception):
    pass


@dataclass
class Quiz:
    id: int
    lecture: str
    title: str
    state: str
    mode: str
    timeout_sec: int | None
    created_at: float

    @property
    def is_open(self) -> bool:
        return self.state == "open"

    @property
    def graded(self) -> bool:
        return self.mode == "graded"


@dataclass
class Attempt:
    id: int
    quiz_id: int
    ticket_token: str
    login: str
    full_name: str
    is_test: bool
    started_at: float
    deadline_at: float | None
    submitted_at: float | None

    @property
    def submitted(self) -> bool:
        return self.submitted_at is not None

    def expired(self, now: float) -> bool:
        return self.deadline_at is not None and now > self.deadline_at


def new_token() -> str:
    return "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(TOKEN_LEN))


def pretty_token(token: str) -> str:
    """Как код печатается на бумаге: KM4P-2QXZ."""
    return f"{token[:4]}-{token[4:]}" if len(token) == TOKEN_LEN else token


def normalize_token(raw: str) -> str:
    return "".join(ch for ch in raw.upper() if ch in TOKEN_ALPHABET)


def _casefold(value: str | None) -> str:
    return value.casefold() if value else ""


class Store:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        # lower() и LIKE в SQLite сворачивают регистр только у латиницы:
        # «Иванов» так и остаётся «Иванов», и поиск по русской фамилии не нашёл
        # бы ничего. Сворачиваем на стороне Python.
        self._db.create_function("casefold", 1, _casefold, deterministic=True)
        self._db.executescript(SCHEMA.read_text(encoding="utf-8"))
        self._db.commit()
        self._migrate()

    def _migrate(self) -> None:
        """Довести уже существующую базу до текущей схемы.

        Нетривиальная часть одна — уникальность лекции. Раньше по одной лекции
        можно было завести сколько угодно пятиминуток, и такие записи в базах
        уже есть. Пустые дубликаты (без единой попытки) удаляем молча: они
        появились от лишнего нажатия и ничего не хранят. Непустые не трогаем
        вовсе и падаем с внятным текстом — выбирать за преподавателя, чьи
        ответы выкинуть, нельзя.
        """
        with self._lock:
            duplicated = self._db.execute(
                "SELECT lecture FROM quiz GROUP BY lecture HAVING COUNT(*) > 1"
            ).fetchall()

            for row in duplicated:
                quizzes = self._db.execute(
                    "SELECT q.id,"
                    " (SELECT COUNT(*) FROM attempt a WHERE a.quiz_id = q.id) AS attempts"
                    " FROM quiz q WHERE q.lecture = ? ORDER BY q.id",
                    (row["lecture"],),
                ).fetchall()
                used = [q for q in quizzes if q["attempts"]]
                if len(used) > 1:
                    raise StoreError(
                        f"по лекции {row['lecture']} несколько пятиминуток с ответами "
                        f"(id {', '.join(str(q['id']) for q in used)}). Оставьте одну руками: "
                        f"объединять или выкидывать чужие ответы автоматически нельзя"
                    )
                keep = used[0]["id"] if used else quizzes[0]["id"]
                for quiz in quizzes:
                    if quiz["id"] == keep:
                        continue
                    self._db.execute("DELETE FROM ticket WHERE quiz_id = ?", (quiz["id"],))
                    self._db.execute("DELETE FROM quiz WHERE id = ?", (quiz["id"],))

            self._db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS quiz_one_per_lecture ON quiz(lecture)"
            )
            self._db.commit()

    def close(self) -> None:
        with self._lock:
            self._db.close()

    # --- пятиминутки ------------------------------------------------------

    def create_quiz(
        self,
        lecture: str,
        title: str = "",
        *,
        mode: str = "practice",
        timeout_sec: int | None = None,
        now: float | None = None,
    ) -> Quiz:
        now = time.time() if now is None else now
        with self._lock:
            try:
                cur = self._db.execute(
                    "INSERT INTO quiz(lecture, title, state, mode, timeout_sec, created_at)"
                    " VALUES (?, ?, 'closed', ?, ?, ?)",
                    (lecture, title, mode, timeout_sec, now),
                )
            except sqlite3.IntegrityError:
                raise StoreError(f"по лекции {lecture} пятиминутка уже есть") from None
            self._db.commit()
            return self.get_quiz(int(cur.lastrowid))

    def quiz_for_lecture(self, lecture: str) -> Quiz | None:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM quiz WHERE lecture = ?", (lecture,)
            ).fetchone()
        return _quiz(row) if row else None

    def get_quiz(self, quiz_id: int) -> Quiz:
        with self._lock:
            row = self._db.execute("SELECT * FROM quiz WHERE id = ?", (quiz_id,)).fetchone()
        if row is None:
            raise StoreError(f"пятиминутки {quiz_id} нет")
        return _quiz(row)

    def list_quizzes(self) -> list[Quiz]:
        with self._lock:
            rows = self._db.execute("SELECT * FROM quiz ORDER BY id DESC").fetchall()
        return [_quiz(r) for r in rows]

    def update_quiz(
        self,
        quiz_id: int,
        *,
        state: str | None = None,
        mode: str | None = None,
        timeout_sec: int | None = None,
        touch_timeout: bool = False,
    ) -> Quiz:
        sets, args = [], []
        if state is not None:
            if state not in ("open", "closed"):
                raise StoreError(f"неизвестное состояние {state!r}")
            sets.append("state = ?")
            args.append(state)
        if mode is not None:
            if mode not in ("practice", "graded"):
                raise StoreError(f"неизвестный режим {mode!r}")
            sets.append("mode = ?")
            args.append(mode)
        if touch_timeout:
            sets.append("timeout_sec = ?")
            args.append(timeout_sec)
        if sets:
            args.append(quiz_id)
            with self._lock:
                self._db.execute(f"UPDATE quiz SET {', '.join(sets)} WHERE id = ?", args)
                self._db.commit()
        return self.get_quiz(quiz_id)

    # --- билеты -----------------------------------------------------------

    def issue_tickets(self, quiz_id: int, count: int, *, now: float | None = None) -> list[str]:
        now = time.time() if now is None else now
        self.get_quiz(quiz_id)
        tokens: list[str] = []
        with self._lock:
            for _ in range(count):
                for _attempt in range(20):
                    token = new_token()
                    try:
                        self._db.execute(
                            "INSERT INTO ticket(token, quiz_id, issued_at) VALUES (?, ?, ?)",
                            (token, quiz_id, now),
                        )
                    except sqlite3.IntegrityError:
                        continue
                    tokens.append(token)
                    break
                else:  # pragma: no cover - 20 подряд коллизий не бывает
                    raise StoreError("не удалось выдать уникальный билет")
            self._db.commit()
        return tokens

    def tickets_for(self, quiz_id: int) -> list[sqlite3.Row]:
        with self._lock:
            return self._db.execute(
                "SELECT * FROM ticket WHERE quiz_id = ? ORDER BY issued_at, token", (quiz_id,)
            ).fetchall()

    def get_ticket(self, token: str) -> sqlite3.Row | None:
        with self._lock:
            return self._db.execute("SELECT * FROM ticket WHERE token = ?", (token,)).fetchone()

    # --- попытки ----------------------------------------------------------

    def get_attempt(self, attempt_id: int) -> Attempt | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM attempt WHERE id = ?", (attempt_id,)).fetchone()
        return _attempt(row) if row else None

    def attempt_by_login(self, quiz_id: int, login: str) -> Attempt | None:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM attempt WHERE quiz_id = ? AND login = ?", (quiz_id, login)
            ).fetchone()
        return _attempt(row) if row else None

    def redeem(
        self,
        token: str,
        *,
        login: str,
        full_name: str,
        is_test: bool,
        questions: list[tuple[str, str]],
        timeout_sec: int | None,
        now: float | None = None,
    ) -> Attempt:
        """Погасить билет и создать попытку.

        Если у этого логина уже есть попытка на эту пятиминутку, она и
        возвращается: студент, подобравший второй билет, не начинает заново,
        а второй билет остаётся непогашенным.
        """
        now = time.time() if now is None else now
        with self._lock:
            ticket = self._db.execute("SELECT * FROM ticket WHERE token = ?", (token,)).fetchone()
            if ticket is None:
                raise StoreError("билет не выдавался")

            existing = self._db.execute(
                "SELECT * FROM attempt WHERE quiz_id = ? AND login = ?",
                (ticket["quiz_id"], login),
            ).fetchone()
            if existing is not None:
                return _attempt(existing)

            if ticket["redeemed_at"] is not None:
                raise StoreError("билет уже использован")

            deadline = now + timeout_sec if timeout_sec else None
            cur = self._db.execute(
                "INSERT INTO attempt(quiz_id, ticket_token, login, full_name, is_test,"
                " started_at, deadline_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    ticket["quiz_id"],
                    token,
                    login,
                    full_name,
                    1 if is_test else 0,
                    now,
                    deadline,
                ),
            )
            attempt_id = int(cur.lastrowid)
            self._db.executemany(
                "INSERT INTO answer(attempt_id, position, question_id, kind, shown_at)"
                " VALUES (?, ?, ?, ?, ?)",
                [(attempt_id, i, qid, kind, now) for i, (qid, kind) in enumerate(questions)],
            )
            self._db.execute(
                "UPDATE ticket SET redeemed_at = ?, attempt_id = ? WHERE token = ?",
                (now, attempt_id, token),
            )
            self._db.commit()
            row = self._db.execute("SELECT * FROM attempt WHERE id = ?", (attempt_id,)).fetchone()
        return _attempt(row)

    def answers_for(self, attempt_id: int) -> list[sqlite3.Row]:
        with self._lock:
            return self._db.execute(
                "SELECT * FROM answer WHERE attempt_id = ? ORDER BY position", (attempt_id,)
            ).fetchall()

    def record_answer(
        self,
        attempt_id: int,
        question_id: str,
        *,
        choice: int | None = None,
        text: str | None = None,
        is_correct: bool | None = None,
        now: float | None = None,
    ) -> None:
        now = time.time() if now is None else now
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM answer WHERE attempt_id = ? AND question_id = ?",
                (attempt_id, question_id),
            ).fetchone()
            if row is None:
                raise StoreError(f"вопроса {question_id} нет в этой попытке")
            already = row["answered_at"] is not None
            self._db.execute(
                "UPDATE answer SET choice = ?, text = ?, is_correct = ?, answered_at = ?,"
                " changes = changes + ? WHERE id = ?",
                (
                    choice,
                    text,
                    None if is_correct is None else int(is_correct),
                    now,
                    1 if already else 0,
                    row["id"],
                ),
            )
            self._db.commit()

    def submit(self, attempt_id: int, *, now: float | None = None) -> None:
        now = time.time() if now is None else now
        with self._lock:
            self._db.execute(
                "UPDATE attempt SET submitted_at = ? WHERE id = ? AND submitted_at IS NULL",
                (now, attempt_id),
            )
            self._db.commit()

    # --- судейство --------------------------------------------------------

    def enqueue_judgement(self, answer_id: int, *, now: float | None = None) -> None:
        now = time.time() if now is None else now
        with self._lock:
            self._db.execute(
                "INSERT INTO judgement(answer_id, status, updated_at, next_try_at)"
                " VALUES (?, 'queued', ?, ?)"
                " ON CONFLICT(answer_id) DO UPDATE SET status='queued', updated_at=excluded.updated_at",
                (answer_id, now, now),
            )
            self._db.commit()

    def claim_judgement(self, *, now: float | None = None) -> sqlite3.Row | None:
        """Забрать одну задачу из очереди. Атомарно — как в classroom."""
        now = time.time() if now is None else now
        with self._lock:
            row = self._db.execute(
                "UPDATE judgement SET status = 'running', tries = tries + 1, updated_at = ?"
                " WHERE answer_id = ("
                "   SELECT answer_id FROM judgement"
                "   WHERE status = 'queued' AND next_try_at <= ?"
                "   ORDER BY next_try_at LIMIT 1)"
                " RETURNING *",
                (now, now),
            ).fetchone()
            self._db.commit()
        return row

    def finish_judgement(
        self,
        answer_id: int,
        *,
        is_correct: bool | None,
        rationale: str = "",
        error: str = "",
        now: float | None = None,
    ) -> None:
        now = time.time() if now is None else now
        with self._lock:
            row = self._db.execute(
                "SELECT tries FROM judgement WHERE answer_id = ?", (answer_id,)
            ).fetchone()
            tries = row["tries"] if row else 0
            if error:
                give_up = tries >= MAX_JUDGE_TRIES
                self._db.execute(
                    "UPDATE judgement SET status = ?, error = ?, updated_at = ?, next_try_at = ?"
                    " WHERE answer_id = ?",
                    (
                        "error" if give_up else "queued",
                        error,
                        now,
                        now + min(60.0, 2.0**tries),
                        answer_id,
                    ),
                )
            else:
                self._db.execute(
                    "UPDATE judgement SET status = 'done', is_correct = ?, rationale = ?,"
                    " error = '', updated_at = ? WHERE answer_id = ?",
                    (None if is_correct is None else int(is_correct), rationale, now, answer_id),
                )
                self._db.execute(
                    "UPDATE answer SET is_correct = ? WHERE id = ?",
                    (None if is_correct is None else int(is_correct), answer_id),
                )
            self._db.commit()

    def judgements_for(self, attempt_id: int) -> dict[int, sqlite3.Row]:
        with self._lock:
            rows = self._db.execute(
                "SELECT j.* FROM judgement j JOIN answer a ON a.id = j.answer_id"
                " WHERE a.attempt_id = ?",
                (attempt_id,),
            ).fetchall()
        return {r["answer_id"]: r for r in rows}

    def judge_queue_stats(self) -> dict[str, int]:
        """Сколько ответов в каком состоянии судейства — по всем пятиминуткам.

        Нужно, чтобы «судья работает» можно было проверить снаружи, не заходя
        под преподавательским токеном: очередь, которая не пустеет, и растущее
        число ошибок видны в /healthz.
        """
        with self._lock:
            rows = self._db.execute(
                "SELECT status, COUNT(*) AS n FROM judgement GROUP BY status"
            ).fetchall()
        stats = {"queued": 0, "running": 0, "done": 0, "error": 0}
        for row in rows:
            stats[row["status"]] = row["n"]
        return stats

    def judge_failures(self, quiz_id: int) -> list[sqlite3.Row]:
        with self._lock:
            return self._db.execute(
                "SELECT j.*, a.attempt_id, a.question_id FROM judgement j"
                " JOIN answer a ON a.id = j.answer_id"
                " JOIN attempt t ON t.id = a.attempt_id"
                " WHERE t.quiz_id = ? AND j.status = 'error'",
                (quiz_id,),
            ).fetchall()

    # --- аналитика --------------------------------------------------------

    def attempts_table(self, quiz_id: int, query: str = "") -> list[dict]:
        """Строки таблицы попыток. Поиск идёт и по ФИО, и по коду билета."""
        sql = (
            "SELECT t.*,"
            " (SELECT COUNT(*) FROM answer a WHERE a.attempt_id = t.id) AS total,"
            " (SELECT COUNT(*) FROM answer a WHERE a.attempt_id = t.id AND a.answered_at IS NOT NULL) AS answered,"
            " (SELECT COUNT(*) FROM answer a WHERE a.attempt_id = t.id AND a.is_correct = 1) AS correct,"
            " (SELECT COUNT(*) FROM answer a JOIN judgement j ON j.answer_id = a.id"
            "    WHERE a.attempt_id = t.id AND j.status IN ('queued','running')) AS pending"
            " FROM attempt t WHERE t.quiz_id = ?"
        )
        args: list = [quiz_id]
        if query.strip():
            needle = f"%{_casefold(query.strip())}%"
            clauses = ["casefold(t.full_name) LIKE ?", "casefold(t.login) LIKE ?"]
            args += [needle, needle]
            token = normalize_token(query)
            if token:
                # Условие по билету добавляется, только если в запросе вообще
                # есть символы кода. Прежняя «заведомо ложная» заглушка
                # содержала NUL, а SQLite обрезает шаблон по нему — из-за чего
                # поиск по русскому имени возвращал вообще всех.
                clauses.append("t.ticket_token LIKE ?")
                args.append(f"%{token}%")
            sql += f" AND ({' OR '.join(clauses)})"
        sql += " ORDER BY t.started_at"

        with self._lock:
            rows = self._db.execute(sql, args).fetchall()

        out = []
        for r in rows:
            duration = (r["submitted_at"] - r["started_at"]) if r["submitted_at"] else None
            out.append(
                {
                    "id": r["id"],
                    "full_name": r["full_name"],
                    "login": r["login"],
                    "ticket": pretty_token(r["ticket_token"]),
                    "is_test": bool(r["is_test"]),
                    "started_at": r["started_at"],
                    "submitted_at": r["submitted_at"],
                    "duration": duration,
                    "answered": r["answered"],
                    "total": r["total"],
                    "correct": r["correct"],
                    "pending": r["pending"],
                }
            )
        return out

    def question_summary(self, quiz_id: int) -> list[dict]:
        """Сводка по вопросам банка: сколько раз достался, доля верных, медиана времени."""
        with self._lock:
            rows = self._db.execute(
                "SELECT a.question_id, a.kind, a.is_correct, a.answered_at, a.shown_at"
                " FROM answer a JOIN attempt t ON t.id = a.attempt_id WHERE t.quiz_id = ?",
                (quiz_id,),
            ).fetchall()

        buckets: dict[str, dict] = {}
        for r in rows:
            b = buckets.setdefault(
                r["question_id"], {"question_id": r["question_id"], "kind": r["kind"],
                                   "shown": 0, "answered": 0, "correct": 0, "times": []}
            )
            b["shown"] += 1
            if r["answered_at"] is not None:
                b["answered"] += 1
                b["times"].append(r["answered_at"] - r["shown_at"])
            if r["is_correct"] == 1:
                b["correct"] += 1

        out = []
        for b in buckets.values():
            times = sorted(b["times"])
            b["median_time"] = times[len(times) // 2] if times else None
            b["share_correct"] = (b["correct"] / b["answered"]) if b["answered"] else None
            b.pop("times")
            out.append(b)
        out.sort(key=lambda b: (b["share_correct"] is None, b["share_correct"] or 0))
        return out

    def durations(self, quiz_id: int) -> list[float]:
        with self._lock:
            rows = self._db.execute(
                "SELECT submitted_at - started_at AS d FROM attempt"
                " WHERE quiz_id = ? AND submitted_at IS NOT NULL",
                (quiz_id,),
            ).fetchall()
        return sorted(r["d"] for r in rows)


def _quiz(row: sqlite3.Row) -> Quiz:
    return Quiz(
        id=row["id"],
        lecture=row["lecture"],
        title=row["title"],
        state=row["state"],
        mode=row["mode"],
        timeout_sec=row["timeout_sec"],
        created_at=row["created_at"],
    )


def _attempt(row: sqlite3.Row) -> Attempt:
    return Attempt(
        id=row["id"],
        quiz_id=row["quiz_id"],
        ticket_token=row["ticket_token"],
        login=row["login"],
        full_name=row["full_name"],
        is_test=bool(row["is_test"]),
        started_at=row["started_at"],
        deadline_at=row["deadline_at"],
        submitted_at=row["submitted_at"],
    )
