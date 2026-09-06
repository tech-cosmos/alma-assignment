from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import COOKIE_NAME, CurrentUser, SessionDep, SettingsDep
from app.core.security import create_access_token
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest
from app.schemas.user import UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserRead)
async def login(
    body: LoginRequest, response: Response, session: SessionDep, settings: SettingsDep
) -> UserRead:
    user = await AuthService(UserRepository(session)).authenticate(body.email, body.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(
        user.id, secret=settings.jwt_secret, expires_minutes=settings.jwt_expires_minutes
    )
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.jwt_expires_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return UserRead.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(_: CurrentUser, response: Response, settings: SettingsDep) -> None:
    response.delete_cookie(
        COOKIE_NAME, httponly=True, secure=settings.cookie_secure, samesite="lax", path="/"
    )


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
