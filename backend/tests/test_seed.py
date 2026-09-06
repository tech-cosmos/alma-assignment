from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.repositories.user import UserRepository
from app.seed import seed


async def test_seed_is_idempotent(db_session: AsyncSession) -> None:
    await seed()
    await seed()
    user = await UserRepository(db_session).get_by_email("attorney@example.com")
    assert user is not None
    assert verify_password("password123", user.password_hash)
