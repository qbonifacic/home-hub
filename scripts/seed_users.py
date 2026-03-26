"""Seed initial users: dj and wife."""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bcrypt
from sqlalchemy import select

from backend.database import async_session
from backend.models.user import User
from backend.config import settings


async def seed():
    async with async_session() as db:
        # Check if users already exist
        result = await db.execute(select(User))
        existing = result.scalars().all()
        if existing:
            print(f"Users already exist: {[u.username for u in existing]}")
            return

        # Create DJ
        dj_hash = bcrypt.hashpw(settings.dj_password.encode(), bcrypt.gensalt()).decode()
        dj = User(
            username="dj",
            password_hash=dj_hash,
            display_name="DJ",
            api_key=settings.q_api_key,
        )
        db.add(dj)

        # Create wife
        wife_hash = bcrypt.hashpw(settings.wife_password.encode(), bcrypt.gensalt()).decode()
        wife = User(
            username="wife",
            password_hash=wife_hash,
            display_name="Angela",
        )
        db.add(wife)

        await db.commit()
        print("Seeded users: dj (with API key), wife")


if __name__ == "__main__":
    asyncio.run(seed())
