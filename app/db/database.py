from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Build the database URL safely.
# URL.create handles special characters in passwords.
DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    database=settings.postgres_db,
)


# Asynchronous SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


# Async database session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Declarative base for ORM models
class Base(DeclarativeBase):
    pass


# FastAPI dependency for database sessions
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# Database connectivity check
async def check_db_connection() -> bool:
    from sqlalchemy import text

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    return True


# Dispose database connections during application shutdown
async def close_db_connection() -> None:
    await engine.dispose()
