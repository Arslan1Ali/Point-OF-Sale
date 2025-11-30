import asyncio
import pathlib
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

async def main() -> None:
    from app.infrastructure.auth.password_hasher import PasswordHasher
    from app.infrastructure.db.repositories.user_repository import UserRepository
    from app.infrastructure.db.session import async_session_factory

    async with async_session_factory() as session:
        repo = UserRepository(session)
        user = await repo.get_by_email("admin@retailpos.com")
        
        if not user:
            print("Admin user not found!")
            return

        print(f"Found admin user: {user.id}")
        
        hasher = PasswordHasher()
        new_hash = hasher.hash("AdminPass123!")
        
        # Manually update the model to avoid use case complexity for this fix
        # But we should use the repository update if possible, or just SQL
        
        # Let's try to update via repository if we can modify the entity
        # The entity is immutable (dataclass(slots=True)), so we might need to create a new instance or use a method
        # User entity has set_password_hash method?
        
        # Let's check User entity again.
        # It has set_password_hash?
        # The use case used user.set_password_hash(hashed)
        
        # Wait, the User entity I read earlier:
        # @dataclass(slots=True)
        # class User:
        # ...
        # def deactivate(self) -> None: ...
        
        # I didn't see set_password_hash in the first 50 lines. Let me assume it exists or I'll check.
        # Actually, I'll just use direct SQL update to be safe and quick.
        
        from sqlalchemy import text
        await session.execute(
            text("UPDATE users SET password_hash = :ph WHERE id = :id"),
            {"ph": new_hash, "id": user.id}
        )
        await session.commit()
        print("Password reset to 'AdminPass123!'")

if __name__ == "__main__":
    asyncio.run(main())
