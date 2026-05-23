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
    # Internal Railway URLs (.railway.internal) don't need SSL.
    # External proxy URLs (roundhouse.proxy.rlwy.net) require SSL.
    _is_internal = ".railway.internal" in _raw_url
    import ssl as _ssl_mod
    _ssl_ctx = None if _is_internal else _ssl_mod.create_default_context()
    if _ssl_ctx:
        _ssl_ctx.check_hostname = False
        _ssl_ctx.verify_mode = _ssl_mod.CERT_NONE
    _engine_kwargs: dict = {
        "pool_size": 3,
        "max_overflow": 5,
        "pool_timeout": 20,
        "connect_args": {"ssl": _ssl_ctx, "timeout": 10} if not _is_internal else {"timeout": 10},
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
