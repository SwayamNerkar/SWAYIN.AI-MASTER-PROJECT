import logging
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger("swayin")

Base = declarative_base()

# Safe driver check for async engine
has_async_driver = False
db_url = settings.DATABASE_URL

try:
    import asyncpg
    has_async_driver = True
except ImportError:
    try:
        import aiosqlite
        db_url = "sqlite+aiosqlite:///./swayin.db"
        has_async_driver = True
    except ImportError:
        has_async_driver = False

if has_async_driver:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    engine = create_async_engine(db_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_db():
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
else:
    # Synchronous SQLite fallback if no async DB drivers are installed
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    db_url = "sqlite:///./swayin.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    async def init_db():
        Base.metadata.create_all(bind=engine)

    async def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
