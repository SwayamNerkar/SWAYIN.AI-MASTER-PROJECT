import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add backend directory to sys.path to allow running standalone or via uvicorn
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.logging import logger
from app.api.router import api_router
from app.database.session import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION} [{settings.ENV}]")
    logger.info(f"Data Feed Mode: {settings.DATA_FEED_MODE} | Broker Adapter: {settings.BROKER_ADAPTER}")
    
    # Initialize database tables
    await init_db()
    logger.info("Database schemas initialized.")
    
    yield
    
    logger.info("Shutting down SWAYIN.AI backend services.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-Based Intraday Options Signal & Market Intelligence System (NIFTY 50 & SENSEX)",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "system": settings.APP_NAME,
        "status": "ONLINE",
        "docs_url": "/docs",
        "api_v1_health": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
