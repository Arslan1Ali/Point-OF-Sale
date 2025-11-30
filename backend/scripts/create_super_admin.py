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
            # Create Super Admin
            user = await use_case.execute(
                CreateUserInput(
                    email="superadmin@pos.com",
                    password="SuperSecretPassword123!",
                    role=UserRole.SUPER_ADMIN,
                )
            )
            await session.commit()
            print(f"SUCCESS: Created SuperAdmin user.")
            print(f"Email: {user.email}")
            print(f"Password: SuperSecretPassword123!")
        except ConflictError:
            await session.rollback()
            print("SuperAdmin user already exists.")
            print("Email: superadmin@pos.com")
            print("Password: SuperSecretPassword123! (If not changed)")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
