from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from backend.core.config import settings


async_engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
async_session_pool = async_sessionmaker(async_engine, expire_on_commit=False)

class Base(DeclarativeBase):
    """Abstract structural base for all relational tables."""
    pass

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider yielding non-blocking SQL connection states."""
    async with async_session_pool() as session:
        yield session