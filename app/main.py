"""
Antony HFT - FastAPI Application
================================

High-Frequency Trading Backend for NSE Options
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.redis import RedisClient
from app.db.postgres import PostgresClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    # Startup
    try:
        await RedisClient.get_pool().ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        
    try:
        await PostgresClient.create_pool()
        await PostgresClient.init_db()
        logger.info("PostgreSQL connected")
    except Exception as e:
        logger.error(f"Postgres connection failed: {e}")
        
    yield
    
    # Shutdown
    await RedisClient.close_pool()
    await PostgresClient.close_pool()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.auth import router as auth_router
from app.api.feed import router as feed_router
from app.api.stream import router as stream_router
from app.api.instrument import router as instrument_router
from app.api.gtt import router as gtt_router
from app.api.portfolio import router as portfolio_router

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(feed_router, prefix=settings.API_V1_STR)
app.include_router(stream_router, prefix=settings.API_V1_STR)
app.include_router(instrument_router, prefix=settings.API_V1_STR)
app.include_router(gtt_router, prefix=settings.API_V1_STR)
app.include_router(portfolio_router, prefix=settings.API_V1_STR)


@app.get("/callback")
async def callback(code: str):
    """OAuth callback handler"""
    from app.services.upstox_auth import UpstoxAuthService
    try:
        access_token = await UpstoxAuthService.generate_access_token(code)
        return {"message": "Login successful", "access_token": access_token}
    except Exception as e:
        return {"error": str(e)}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_status = "down"
    postgres_status = "down"
    
    try:
        if await RedisClient.get_pool().ping():
            redis_status = "up"
    except Exception:
        pass
        
    try:
        async with PostgresClient.get_pool().acquire() as conn:
            await conn.fetchval("SELECT 1")
            postgres_status = "up"
    except Exception:
        pass

    return {
        "status": "ok",
        "redis": redis_status,
        "postgres": postgres_status
    }
