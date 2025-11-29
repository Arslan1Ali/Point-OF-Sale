from __future__ import annotations

import asyncio
import pathlib
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

async def main() -> None:
    from app.application.auth.use_cases.create_user import CreateUserInput, CreateUserUseCase
    from app.domain.auth.entities import UserRole
    from app.domain.common.errors import ConflictError
    from app.infrastructure.auth.password_hasher import PasswordHasher
    from app.infrastructure.db.repositories.user_repository import UserRepository
    from app.infrastructure.db.session import async_session_factory

    async with async_session_factory() as session:
        use_case = CreateUserUseCase(UserRepository(session), PasswordHasher())
        try:
            user = await use_case.execute(
                CreateUserInput(
                    email="admin@retailpos.com",
                    password="AdminPass123!",
                    role=UserRole.ADMIN,
                )
            )
            await session.commit()
            print(f"Created admin user {user.email} (id={user.id})")
        except ConflictError:
            await session.rollback()
            print("Admin user already exists.")


if __name__ == "__main__":
    asyncio.run(main())
