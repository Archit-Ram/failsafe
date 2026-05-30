"""Password hashing + JWT helpers.

We call ``bcrypt`` directly instead of going through passlib because
recent bcrypt 4.x releases broke passlib's auto-detection on Python
3.12+. Bcrypt only operates on the first 72 bytes of the password, so
we truncate explicitly to keep the behaviour deterministic.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from .config import get_settings

_settings = get_settings()
_BCRYPT_MAX_BYTES = 72


def _to_bytes(password: str) -> bytes:
    encoded = password.encode("utf-8")
    return encoded[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bytes(password), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    expires = datetime.now(tz=timezone.utc) + timedelta(
        minutes=_settings.access_token_minutes
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expires}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token, _settings.jwt_secret, algorithms=[_settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise ValueError(str(exc)) from exc
