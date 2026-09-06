"""Dependency injection: settings, DB session, adapters, current user."""

import importlib
from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.email.base import EmailAdapter
from app.adapters.storage.base import StorageAdapter
from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user import UserRepository

COOKIE_NAME = "access_token"

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _load_adapter(package: str, provider: str, settings: Settings) -> object:
    """Import ``app.adapters.<package>.<provider>`` and call its ``create_adapter``."""
    try:
        module = importlib.import_module(f"app.adapters.{package}.{provider}")
    except ModuleNotFoundError as exc:
        raise RuntimeError(f"No {package} adapter named {provider!r} is installed.") from exc
    factory = getattr(module, "create_adapter", None)
    if factory is None:
        raise RuntimeError(f"app.adapters.{package}.{provider} lacks create_adapter().")
    return factory(settings)


def get_email_adapter(request: Request, settings: SettingsDep) -> EmailAdapter:
    cached = getattr(request.app.state, "email_adapter", None)
    if cached is None:
        cached = _load_adapter("email", settings.email_provider, settings)
        request.app.state.email_adapter = cached
    return cast(EmailAdapter, cached)


def get_storage_adapter(request: Request, settings: SettingsDep) -> StorageAdapter:
    cached = getattr(request.app.state, "storage_adapter", None)
    if cached is None:
        cached = _load_adapter("storage", settings.storage_provider, settings)
        request.app.state.storage_adapter = cached
    return cast(StorageAdapter, cached)


EmailDep = Annotated[EmailAdapter, Depends(get_email_adapter)]
StorageDep = Annotated[StorageAdapter, Depends(get_storage_adapter)]


def _extract_token(request: Request) -> str | None:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    auth = request.headers.get("authorization", "")
    scheme, _, value = auth.partition(" ")
    if scheme.lower() == "bearer" and value:
        return value
    return None


async def get_current_user(request: Request, session: SessionDep, settings: SettingsDep) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = _extract_token(request)
    if token is None:
        raise unauthorized
    user_id = decode_access_token(token, secret=settings.jwt_secret)
    if user_id is None:
        raise unauthorized
    user = await UserRepository(session).get(user_id)
    if user is None:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
