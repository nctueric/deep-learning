"""Database engine and session factory.

Engine is lazily initialized to allow running without a database
(e.g., for demo mode, tests, or when only using in-memory features).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Lazy initialization — only created when actually needed
_engine = None
_async_session = None


def get_engine():
    global _engine
    if _engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine
        from portfolio_tracker.config.settings import settings
        _engine = create_async_engine(
            settings.database.url,
            echo=settings.database.echo,
            pool_size=settings.database.pool_size,
        )
    return _engine


def get_session_factory():
    global _async_session
    if _async_session is None:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
        _async_session = async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _async_session


async def get_session():
    factory = get_session_factory()
    async with factory() as session:
        yield session
