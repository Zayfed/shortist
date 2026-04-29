import os

os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASS", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("SECRET", "test-secret-do-not-use-in-prod")

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import Base, get_db


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"
TEST_USER_ID = 1

SECOND_USER_EMAIL = "second@example.com"
SECOND_USER_PASSWORD = "secondpassword123"
SECOND_USER_ID = 2


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    yield factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(session_factory) -> AsyncSession:
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(session_factory) -> AsyncClient:
    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


async def _register_and_login(client, user_id: int, email: str, password: str) -> str:
    response = await client.post(
        "/auth/register",
        json={"id": user_id, "email": email, "password": password},
    )
    assert response.status_code == 201

    response = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 204
    return response.cookies["shortist"]


@pytest_asyncio.fixture
async def auth_token(async_client) -> str:
    return await _register_and_login(
        async_client, TEST_USER_ID, TEST_USER_EMAIL, TEST_USER_PASSWORD
    )


@pytest_asyncio.fixture
async def second_auth_token(async_client) -> str:
    return await _register_and_login(
        async_client, SECOND_USER_ID, SECOND_USER_EMAIL, SECOND_USER_PASSWORD
    )
