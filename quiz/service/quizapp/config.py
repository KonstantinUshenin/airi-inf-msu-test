"""Настройки сервиса. Всё из окружения, ничего из репозитория.

Имена ключей для модели намеренно те же, что уже приняты в этом репозитории
(`tools/review_seminars.py`): REVIEW_MODEL и REVIEW_API_KEY / DEEPSEEK_API_KEY.
Заводить третью конвенцию ради одного сервиса незачем.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BANKS = REPO_ROOT / "quiz" / "banks"
DEFAULT_STATE = Path.home() / ".local" / "state" / "quiz"


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    state_dir: Path = field(default_factory=lambda: Path(os.environ.get("QUIZ_STATE_DIR", DEFAULT_STATE)))
    banks_dir: Path = field(default_factory=lambda: Path(os.environ.get("QUIZ_BANKS_DIR", DEFAULT_BANKS)))
    base_url: str = field(default_factory=lambda: os.environ.get("QUIZ_BASE_URL", "http://127.0.0.1:8391").rstrip("/"))

    # Преподавательский контур защищён своим секретом, а не студенческой сессией.
    teacher_token: str = field(default_factory=lambda: os.environ.get("QUIZ_TEACHER_TOKEN", ""))
    secret_key: str = field(default_factory=lambda: os.environ.get("QUIZ_SECRET_KEY", ""))

    # test — вход по введённому ФИО, для разработки и для первой лекции,
    # пока не заведено приложение в authentik.
    auth_mode: str = field(default_factory=lambda: os.environ.get("QUIZ_AUTH_MODE", "test"))
    oidc_issuer: str = field(default_factory=lambda: os.environ.get("QUIZ_OIDC_ISSUER", ""))
    oidc_client_id: str = field(default_factory=lambda: os.environ.get("QUIZ_OIDC_CLIENT_ID", ""))
    oidc_client_secret: str = field(default_factory=lambda: os.environ.get("QUIZ_OIDC_CLIENT_SECRET", ""))
    oidc_scopes: str = field(default_factory=lambda: os.environ.get("QUIZ_OIDC_SCOPES", "openid profile email"))
    # У authentik это поле «username» аккаунта — та же конвенция, что у роли
    # jupyterhub в msu/infra.
    oidc_username_claim: str = field(default_factory=lambda: os.environ.get("QUIZ_OIDC_USERNAME_CLAIM", "preferred_username"))

    default_timeout_sec: int = field(default_factory=lambda: int(os.environ.get("QUIZ_DEFAULT_TIMEOUT_SEC", "120")))

    judge_enabled: bool = field(default_factory=lambda: _bool("QUIZ_JUDGE_ENABLED", True))
    judge_poll_sec: float = field(default_factory=lambda: float(os.environ.get("QUIZ_JUDGE_POLL_SEC", "2")))
    llm_base_url: str = field(default_factory=lambda: os.environ.get("QUIZ_LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/"))
    llm_model: str = field(default_factory=lambda: os.environ.get("REVIEW_MODEL", "deepseek-v4-pro"))
    llm_api_key: str = field(
        default_factory=lambda: os.environ.get("REVIEW_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
    )
    llm_timeout_sec: float = field(default_factory=lambda: float(os.environ.get("QUIZ_LLM_TIMEOUT_SEC", "60")))

    def __post_init__(self) -> None:
        self.state_dir = Path(self.state_dir)
        self.banks_dir = Path(self.banks_dir)
        if self.auth_mode not in ("test", "oidc"):
            raise SystemExit(f"QUIZ_AUTH_MODE={self.auth_mode!r}: ожидается test или oidc")
        if self.auth_mode == "oidc" and not (self.oidc_issuer and self.oidc_client_id):
            raise SystemExit("режим oidc требует QUIZ_OIDC_ISSUER и QUIZ_OIDC_CLIENT_ID")
        if not self.secret_key:
            # Без ключа в окружении сессии живут до перезапуска. Это допустимо
            # для разработки и недопустимо в проде, поэтому роль его задаёт.
            self.secret_key = secrets.token_urlsafe(32)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @property
    def db_path(self) -> Path:
        return self.state_dir / "quiz.sqlite"

    @property
    def judge_configured(self) -> bool:
        return bool(self.llm_api_key)


def checkout_revision() -> str | None:
    """Короткий хеш коммита, из которого запущен сервис.

    Нужен, чтобы «доехал ли деплой» проверялось снаружи одним запросом, а не
    угадывалось по косвенным признакам: правка вроде порядка вариантов в
    ответах сервиса никак не видна, и убедиться в ней иначе нельзя.

    Читаем .git руками, без вызова git: у сервиса нет ни шелла, ни нужды
    порождать процессы ради одной строки. Нет .git (установка не из чекаута) —
    возвращаем None, это не ошибка.
    """
    for parent in [REPO_ROOT, *REPO_ROOT.parents]:
        dot_git = parent / ".git"
        try:
            if dot_git.is_file():
                # git worktree: .git — файл со строкой «gitdir: <путь>».
                # На сервере чекаут обычный, но разработка идёт в worktree,
                # и без этой ветки версия читалась бы только в проде.
                pointer = dot_git.read_text(encoding="utf-8").strip()
                if not pointer.startswith("gitdir: "):
                    return None
                git_dir = Path(pointer[8:])
                if not git_dir.is_absolute():
                    git_dir = (parent / git_dir).resolve()
            elif dot_git.is_dir():
                git_dir = dot_git
            else:
                continue

            ref = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
            if not ref.startswith("ref: "):
                return ref[:12]  # detached HEAD

            name = ref[5:]
            # У worktree свои ссылки лежат в его каталоге, общие — в основном.
            for base in (git_dir, *git_dir.parents):
                target = base / name
                if target.is_file():
                    return target.read_text(encoding="utf-8").strip()[:12]
                packed = base / "packed-refs"
                if packed.is_file():
                    for line in packed.read_text(encoding="utf-8").splitlines():
                        if line.endswith(" " + name):
                            return line.split()[0][:12]
                if (base / "HEAD").is_file() and base != git_dir:
                    break
            return None
        except OSError:
            return None
    return None
