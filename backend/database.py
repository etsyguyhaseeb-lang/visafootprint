import os
import re
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

_raw_url = os.getenv("DATABASE_URL", "")
if _raw_url:
    # Railway sets postgres:// or postgresql:// — asyncpg needs postgresql+asyncpg://
    DATABASE_URL = re.sub(r"^postgres(ql)?://", "postgresql+asyncpg://", _raw_url)
    # Railway external URLs require SSL; internal URLs work without it.
    # We pass ssl=True so both work safely.
    _engine_kwargs: dict = {
        "pool_size": 5,
        "max_overflow": 10,
        "connect_args": {"ssl": True},
    }
else:
    # Local dev: SQLite
    _db_path = os.getenv("DB_PATH", ".tmp/screening.db")
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite+aiosqlite:///{_db_path}"
    _engine_kwargs = {}

engine = create_async_engine(DATABASE_URL, echo=False, **_engine_kwargs)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
