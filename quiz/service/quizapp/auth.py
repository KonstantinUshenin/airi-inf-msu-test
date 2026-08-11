"""Личность студента: authentik по OIDC, либо тестовая заглушка.

Подпись id_token намеренно не проверяется — и не потому, что «сойдёт»:
токен берётся не из редиректа браузера, а обратным каналом с token endpoint
по TLS, и сразу после этого мы всё равно идём на userinfo с полученным
access-токеном. Именно userinfo и является источником логина и ФИО. Такой
путь не требует ни разбора JWT, ни криптографической зависимости.

Тестовый режим существует, чтобы разработка и первая лекция не ждали
регистрации приложения в auth.ai.msu.ru. Попытки, созданные в нём, помечены
`is_test` и видны такими же преподавателю.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

import httpx
from itsdangerous import BadSignature, URLSafeSerializer

from .config import Settings

SESSION_COOKIE = "quiz_session"
STATE_COOKIE = "quiz_oidc_state"


@dataclass
class Identity:
    login: str
    full_name: str
    is_test: bool


class AuthError(Exception):
    pass


class Sessions:
    """Подписанные куки. Ничего серверного: сессия — это сам логин и ФИО."""

    def __init__(self, secret_key: str) -> None:
        self._s = URLSafeSerializer(secret_key, salt="quiz-session")

    def dump(self, identity: Identity) -> str:
        return self._s.dumps(
            {"l": identity.login, "n": identity.full_name, "t": int(identity.is_test)}
        )

    def load(self, raw: str | None) -> Identity | None:
        if not raw:
            return None
        try:
            data = self._s.loads(raw)
        except BadSignature:
            return None
        return Identity(login=data["l"], full_name=data["n"], is_test=bool(data["t"]))


def test_identity(full_name: str) -> Identity:
    """Логин выводится из ФИО, чтобы повторный вход дал тот же набор вопросов."""
    name = " ".join(full_name.split())
    if not name:
        raise AuthError("не указано ФИО")
    slug = "".join(ch if ch.isalnum() else "-" for ch in name.casefold()).strip("-")
    return Identity(login=f"test:{slug}", full_name=name, is_test=True)


class OidcClient:
    def __init__(self, settings: Settings) -> None:
        self.s = settings
        self._meta: dict | None = None

    async def metadata(self) -> dict:
        if self._meta is None:
            url = f"{self.s.oidc_issuer.rstrip('/')}/.well-known/openid-configuration"
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
            if resp.status_code != 200:
                raise AuthError(f"не читается конфигурация OIDC ({resp.status_code}): {url}")
            self._meta = resp.json()
        return self._meta

    def new_state(self) -> str:
        return secrets.token_urlsafe(24)

    async def authorize_url(self, *, state: str, redirect_uri: str) -> str:
        meta = await self.metadata()
        params = httpx.QueryParams(
            {
                "response_type": "code",
                "client_id": self.s.oidc_client_id,
                "redirect_uri": redirect_uri,
                "scope": self.s.oidc_scopes,
                "state": state,
            }
        )
        return f"{meta['authorization_endpoint']}?{params}"

    async def exchange(self, *, code: str, redirect_uri: str) -> Identity:
        meta = await self.metadata()
        async with httpx.AsyncClient(timeout=30) as client:
            token = await client.post(
                meta["token_endpoint"],
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.s.oidc_client_id,
                    "client_secret": self.s.oidc_client_secret,
                },
                headers={"Accept": "application/json"},
            )
            if token.status_code != 200:
                raise AuthError(f"обмен кода не удался ({token.status_code}): {token.text[:200]}")
            access = token.json().get("access_token")
            if not access:
                raise AuthError("в ответе token endpoint нет access_token")

            info = await client.get(
                meta["userinfo_endpoint"], headers={"Authorization": f"Bearer {access}"}
            )
            if info.status_code != 200:
                raise AuthError(f"userinfo не отвечает ({info.status_code})")
            claims = info.json()

        login = claims.get(self.s.oidc_username_claim) or claims.get("sub")
        if not login:
            raise AuthError(f"в userinfo нет ни {self.s.oidc_username_claim}, ни sub")
        name = claims.get("name") or claims.get("given_name") or login
        return Identity(login=str(login), full_name=str(name), is_test=False)
