"""
PostgreSQL database connection using SQLAlchemy 2.x async engine with asyncpg.
Replaces the Motor/MongoDB database.py.
"""
import os # type: ignore
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker # type: ignore
from sqlalchemy.orm import DeclarativeBase # type: ignore

# ── Connection URL ────────────────────────────────────────────────────────────
# Format: postgresql+asyncpg://user:password@host:port/dbname
PG_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/insurance_platform"
)

# ── Engine & Session ──────────────────────────────────────────────────────────
engine = None
AsyncSessionLocal = None


class Base(DeclarativeBase):
    pass


async def init_db():
    """Create engine, sessionmaker, and all tables."""
    global engine, AsyncSessionLocal
    engine = create_async_engine(PG_URL, echo=False, pool_pre_ping=True)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Import models so Base.metadata knows all tables, then create them
    import models # type: ignore # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅  Connected to PostgreSQL and tables created.")


async def close_db():
    global engine
    if engine:
        await engine.dispose()


def get_db_session() -> AsyncSession:
    """Return a new async session. Use as an async context manager."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return AsyncSessionLocal()
