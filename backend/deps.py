import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Request, HTTPException, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import async_session
from backend.models.user import User, SessionAuth


async def get_db():
    async with async_session() as session:
        yield session


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Authenticate via session cookie or X-API-Key header."""

    # 1. Check API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        result = await db.execute(select(User).where(User.api_key == api_key))
        user = result.scalar_one_or_none()
        if user:
            return user
        raise HTTPException(status_code=401, detail="Invalid API key")

    # 2. Check session cookie
    session_id = request.cookies.get("session_id")
    if session_id:
        result = await db.execute(
            select(SessionAuth).where(
                SessionAuth.id == session_id,
                SessionAuth.expires_at > datetime.now(timezone.utc),
            )
        )
        session = result.scalar_one_or_none()
        if session:
            result = await db.execute(select(User).where(User.id == session.user_id))
            user = result.scalar_one_or_none()
            if user:
                return user

    raise HTTPException(status_code=401, detail="Not authenticated")


async def create_session(db: AsyncSession, user_id: int) -> str:
    """Create a new session and return the session ID."""
    session_id = secrets.token_urlsafe(64)
    session = SessionAuth(
        id=session_id,
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(session)
    await db.commit()
    return session_id


async def delete_session(db: AsyncSession, session_id: str):
    """Delete a session."""
    await db.execute(delete(SessionAuth).where(SessionAuth.id == session_id))
    await db.commit()
