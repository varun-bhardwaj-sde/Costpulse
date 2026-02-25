"""FastAPI dependencies for database sessions and authentication."""

import os
import secrets
from typing import AsyncGenerator, Optional

from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.models.base import async_session_factory


def _get_api_secret_key() -> str:
    """Get API secret key from environment, raising if unset."""
    key = os.environ.get("API_SECRET_KEY")
    if not key:
        raise RuntimeError("API_SECRET_KEY environment variable must be set")
    return key


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def verify_api_key(x_api_key: Optional[str] = Header(default=None)) -> str:
    """Verify API key from request header."""
    api_secret = _get_api_secret_key()
    if not x_api_key or not secrets.compare_digest(x_api_key, api_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key
