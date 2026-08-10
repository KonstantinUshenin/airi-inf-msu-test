"""Инструменты чтения репозитория для агентного ревью.

Ревьюеру мало текста самого семинара: полезное замечание часто рождается из
соседнего файла — `seminars/README.md` с планом курса целиком, конспект в
`lectures/`, правила линтера, README другого семинара. Здесь три инструмента
(`list_files`, `read_file`, `grep`), которые модель вызывает сама через
function calling.

Ограничения жёсткие и намеренные:

- всё резолвится относительно корня репозитория, выход за него запрещён;
- `.git`, `__pycache__` и бинарные каталоги не отдаются;
- у каждого чтения есть потолок, и у сессии целиком тоже — иначе модель
  вытянет в контекст весь репозиторий и упрётся в лимит токенов;
- инструменты только читают. Ничего не пишут и не выполняют.

Ноутбуки отдаются не как JSON, а развёрнутыми в markdown с нумерацией ячеек —
тем же рендером, что и материал на ревью, чтобы ссылки «ячейка 17» совпадали.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from seminar_context import render_notebook

MAX_READ_CHARS = 40_000  # один файл
MAX_TOTAL_CHARS = 300_000  # вся сессия чтения
MAX_MATCHES = 60  # строк выдачи grep
SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints", "node_modules", ".venv"}

TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "Список файлов репозитория по glob-шаблону относительно корня. "
                "Примеры: 'seminars/*', 'seminars/**/*.md', 'lectures/**'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "glob-шаблон"}
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Прочитать текстовый файл репозитория. Ноутбуки .ipynb отдаются "
                "развёрнутыми в markdown с нумерацией ячеек."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "путь от корня репо"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": (
                "Найти строки по регулярному выражению в файлах репозитория. "
                "Полезно, чтобы проверить, разбирается ли понятие в других "
                "семинарах."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "регулярка"},
                    "glob": {
                        "type": "string",
                        "description": "где искать, по умолчанию '**/*'",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
]


class RepoTools:
    """Песочница чтения одного репозитория. Считает израсходованный бюджет."""

    def __init__(self, repo: Path):
        self.repo = repo.resolve()
        self.spent = 0
        self.calls: list[str] = []

    # --- служебное -------------------------------------------------------

    def _resolve(self, path: str) -> Path | None:
        candidate = (self.repo / path).resolve()
        if candidate != self.repo and self.repo not in candidate.parents:
            return None
        if any(part in SKIP_DIRS for part in candidate.parts):
            return None
        return candidate

    def _iter_files(self, pattern: str):
        for path in sorted(self.repo.glob(pattern)):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.relative_to(self.repo).parts):
                continue
            yield path

    def _budget_left(self) -> int:
        return MAX_TOTAL_CHARS - self.spent

    def _spend(self, text: str) -> str:
        room = self._budget_left()
        if room <= 0:
            return "(бюджет чтения исчерпан — опирайся на то, что уже прочитано)"
        if len(text) > room:
            text = text[:room] + "\n…обрезано: бюджет чтения исчерпан…"
        self.spent += len(text)
        return text

    # --- инструменты -----------------------------------------------------

    def list_files(self, pattern: str = "**/*") -> str:
        # Каталоги показываем тоже, со слэшем на конце: без этого запрос
        # 'seminars/*' возвращал один README.md, и модель не видела, какие
        # вообще есть семинары.
        names = []
        for path in sorted(self.repo.glob(pattern)):
            relative = path.relative_to(self.repo)
            if any(part in SKIP_DIRS for part in relative.parts):
                continue
            if path.is_dir():
                names.append(relative.as_posix() + "/")
            elif path.is_file():
                names.append(relative.as_posix())
        if not names:
            return f"по шаблону {pattern!r} ничего не найдено"
        return self._spend("\n".join(names[:400]))

    def read_file(self, path: str) -> str:
        target = self._resolve(path)
        if target is None or not target.is_file():
            return f"файла {path!r} нет в репозитории (или он недоступен)"
        try:
            if target.suffix == ".ipynb":
                text = render_notebook(target)
            else:
                text = target.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            return f"{path!r} — не текстовый файл"
        if len(text) > MAX_READ_CHARS:
            text = text[:MAX_READ_CHARS] + "\n…файл обрезан…"
        return self._spend(text)

    def grep(self, pattern: str, glob: str = "**/*") -> str:
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as error:
            return f"плохая регулярка: {error}"
        out: list[str] = []
        for path in self._iter_files(glob):
            if path.suffix in {".png", ".jpg", ".gif", ".pdf", ".pt"}:
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, ValueError):
                continue
            name = path.relative_to(self.repo).as_posix()
            for number, line in enumerate(lines, start=1):
                if regex.search(line):
                    out.append(f"{name}:{number}: {line.strip()[:200]}")
                    if len(out) >= MAX_MATCHES:
                        out.append("…совпадений больше, показаны первые…")
                        return self._spend("\n".join(out))
        return self._spend("\n".join(out) if out else f"по {pattern!r} совпадений нет")

    def dispatch(self, name: str, arguments: dict) -> str:
        handlers = {
            "list_files": lambda a: self.list_files(a.get("pattern", "**/*")),
            "read_file": lambda a: self.read_file(a.get("path", "")),
            "grep": lambda a: self.grep(a.get("pattern", ""), a.get("glob", "**/*")),
        }
        handler = handlers.get(name)
        if handler is None:
            return f"нет инструмента {name!r}"
        short = ", ".join(f"{k}={v!r}" for k, v in arguments.items())
        self.calls.append(f"{name}({short})")
        return handler(arguments)


def is_glob_safe(pattern: str) -> bool:
    """Шаблон не должен уводить за пределы репозитория."""
    return not pattern.startswith("/") and ".." not in fnmatch.translate(pattern)
