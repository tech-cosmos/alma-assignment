from app.core.security import verify_password
from app.models.user import User
from app.repositories.user import UserRepository


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self._users.get_by_email(email.lower())
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user
