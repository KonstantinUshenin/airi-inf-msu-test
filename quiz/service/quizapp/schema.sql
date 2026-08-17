-- Хранилище пятиминуток. SQLite, как у соседнего classroom: один файл, который
-- копируется и восстанавливается без инструментов, при нагрузке в несколько
-- десятков записей на лекцию.
--
-- Время везде — epoch-секунды (REAL) по серверным часам. Клиентских отметок
-- здесь нет и быть не должно: время на вопрос — главная метрика первых прогонов,
-- и оно не должно правиться из консоли браузера.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Одна лекция — одна пятиминутка. Уникальный индекс создаётся не здесь, а в
-- Store._migrate(): в уже существующих базах есть дубликаты, и их надо сперва
-- разобрать, иначе создание индекса упадёт при старте сервиса.
CREATE TABLE IF NOT EXISTS quiz (
    id          INTEGER PRIMARY KEY,
    lecture     TEXT    NOT NULL,
    title       TEXT    NOT NULL DEFAULT '',
    state       TEXT    NOT NULL DEFAULT 'closed',   -- open | closed
    mode        TEXT    NOT NULL DEFAULT 'practice', -- practice | graded
    timeout_sec INTEGER,                             -- NULL = без таймаута
    created_at  REAL    NOT NULL
);

-- Билет анонимен: ни ФИО, ни группы. Личность приезжает из SSO и связывается
-- с билетом только в момент погашения (docs/adr/0004).
CREATE TABLE IF NOT EXISTS ticket (
    token       TEXT    PRIMARY KEY,
    quiz_id     INTEGER NOT NULL REFERENCES quiz(id) ON DELETE CASCADE,
    issued_at   REAL    NOT NULL,
    redeemed_at REAL,
    attempt_id  INTEGER
);

CREATE INDEX IF NOT EXISTS ticket_by_quiz ON ticket(quiz_id);

CREATE TABLE IF NOT EXISTS attempt (
    id           INTEGER PRIMARY KEY,
    quiz_id      INTEGER NOT NULL REFERENCES quiz(id) ON DELETE CASCADE,
    ticket_token TEXT    NOT NULL REFERENCES ticket(token),
    login        TEXT    NOT NULL,
    full_name    TEXT    NOT NULL,
    is_test      INTEGER NOT NULL DEFAULT 0,
    started_at   REAL    NOT NULL,
    deadline_at  REAL,
    submitted_at REAL
);

-- Один человек — одна попытка на пятиминутку. Второй подобранный билет
-- возвращает ту же попытку, а не начинает новую.
CREATE UNIQUE INDEX IF NOT EXISTS attempt_one_per_login ON attempt(quiz_id, login);

CREATE TABLE IF NOT EXISTS answer (
    id          INTEGER PRIMARY KEY,
    attempt_id  INTEGER NOT NULL REFERENCES attempt(id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    question_id TEXT    NOT NULL,
    kind        TEXT    NOT NULL,        -- mc | open
    shown_at    REAL    NOT NULL,
    answered_at REAL,
    changes     INTEGER NOT NULL DEFAULT 0,
    choice      INTEGER,                 -- исходный индекс варианта в банке
    text        TEXT,
    is_correct  INTEGER                  -- NULL = ещё неизвестно (открытый вопрос)
);

CREATE UNIQUE INDEX IF NOT EXISTS answer_unique ON answer(attempt_id, question_id);

-- Очередь судейства открытых ответов. Отдельная таблица, а не колонка в answer:
-- у судейства своя жизнь (повторы, backoff, ошибка провайдера), и отсутствие
-- вердикта — штатное состояние, а не сбой.
CREATE TABLE IF NOT EXISTS judgement (
    answer_id   INTEGER PRIMARY KEY REFERENCES answer(id) ON DELETE CASCADE,
    status      TEXT    NOT NULL DEFAULT 'queued',  -- queued | running | done | error
    is_correct  INTEGER,
    rationale   TEXT    NOT NULL DEFAULT '',
    tries       INTEGER NOT NULL DEFAULT 0,
    next_try_at REAL    NOT NULL DEFAULT 0,
    error       TEXT    NOT NULL DEFAULT '',
    updated_at  REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS judgement_pending ON judgement(status, next_try_at);
