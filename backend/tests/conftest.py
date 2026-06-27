"""Shared fixtures: an in-memory DB, dependency overrides, and an HTTP client."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.core.database import Base, get_db_session
from backend.core.deps import get_llm_client
from backend.core.models import ChatMessageORM, ConsultationORM, TrainingPlanORM
from backend.main import app
from backend.tests.factories import FakeLLMClient, intake_payload


@pytest_asyncio.fixture
async def engine():
    # Shared single connection (StaticPool) so the in-memory schema/data persists
    # across the route's session and the test's assertion session.
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_maker(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def fake_llm():
    return FakeLLMClient()


@pytest_asyncio.fixture
async def client(session_maker, fake_llm):
    async def _override_db():
        async with session_maker() as session:
            yield session

    async def _override_llm():
        yield fake_llm

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_llm_client] = _override_llm

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def consultation_id(session_maker) -> str:
    """Seed a consultation directly and return its id."""
    async with session_maker() as db:
        consult = ConsultationORM(intake_snapshot=intake_payload())
        db.add(consult)
        await db.commit()
        return consult.id


# Re-export ORM types for convenience in test modules.
__all__ = ["ChatMessageORM", "ConsultationORM", "TrainingPlanORM"]
