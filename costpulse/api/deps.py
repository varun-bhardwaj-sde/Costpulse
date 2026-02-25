"""FastAPI dependencies for database sessions and authentication."""

import os
from typing import AsyncGenerator

from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.models.base import async_session_factory

API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "change_this_secret_key")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def verify_api_key(x_api_key: str = Header(default=None)) -> str:
    """Verify API key from request header."""
    if not x_api_key or x_api_key != API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key
