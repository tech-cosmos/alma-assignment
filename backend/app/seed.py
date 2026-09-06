"""Create (or update) the attorney login from SEED_USER_EMAIL / SEED_USER_PASSWORD.

Run with ``uv run seed`` (or ``python -m app.seed``). Idempotent.
"""

import asyncio
import logging

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.db.session import create_engine, create_session_factory
from app.models.user import User
from app.repositories.user import UserRepository

log = logging.getLogger(__name__)


async def seed() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        async with create_session_factory(engine)() as session:
            repo = UserRepository(session)
            email = settings.seed_user_email.lower()
            user = await repo.get_by_email(email)
            if user is None:
                await repo.add(
                    User(email=email, password_hash=hash_password(settings.seed_user_password))
                )
                log.info("Created attorney user %s", email)
            else:
                user.password_hash = hash_password(settings.seed_user_password)
                log.info("Reset password for existing user %s", email)
            await repo.commit()
    finally:
        await engine.dispose()


def main() -> None:
    configure_logging()
    asyncio.run(seed())


if __name__ == "__main__":
    main()
