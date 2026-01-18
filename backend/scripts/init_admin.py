#!/usr/bin/env python3
"""
Initialize the database with a default admin user.
Run this script once after setting up the database.
"""
import asyncio
import sys
sys.path.insert(0, '..')

from app.database import async_session_maker, init_db
from app.models.user import User, Role
from app.core.security import get_password_hash


async def create_admin():
    """Create default admin user if not exists."""
    await init_db()

    async with async_session_maker() as session:
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("Admin user already exists!")
            return

        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            phone="13800000000",
            hashed_password=get_password_hash("admin123"),
            role=Role.ADMIN.value,
            is_active=True,
            is_online=False,
            created_by="system",
        )
        session.add(admin)
        await session.commit()

        print("=" * 50)
        print("Admin user created successfully!")
        print("=" * 50)
        print(f"Username: admin")
        print(f"Password: admin123")
        print(f"Role: {Role.ADMIN.value}")
        print("=" * 50)
        print("Please change the password after first login!")


if __name__ == "__main__":
    asyncio.run(create_admin())
