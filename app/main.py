from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.db.redis import RedisClient
from app.db.postgres import PostgresClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await RedisClient.get_pool().ping()
    except Exception as e:
        print(f"Redis connection failed: {e}")
        
    try:
        await PostgresClient.create_pool()
        await PostgresClient.init_db()
    except Exception as e:
        print(f"Postgres connection failed: {e}")
        
    yield
    # Shutdown
    await RedisClient.close_pool()
    await PostgresClient.close_pool()

    await PostgresClient.close_pool()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.auth import router as auth_router
app.include_router(auth_router, prefix=settings.API_V1_STR)

from app.api.feed import router as feed_router
app.include_router(feed_router, prefix=settings.API_V1_STR)

from app.api.stream import router as stream_router
app.include_router(stream_router, prefix=settings.API_V1_STR)

from app.api.instrument import router as instrument_router
app.include_router(instrument_router, prefix=settings.API_V1_STR)

@app.get("/callback")
async def callback(code: str):
    from app.services.upstox_auth import UpstoxAuthService
    try:
        access_token = await UpstoxAuthService.generate_access_token(code)
        return {"message": "Login successful", "access_token": access_token}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health")
async def health_check():
    redis_status = "down"
    postgres_status = "down"
    
    try:
        if await RedisClient.get_pool().ping():
            redis_status = "up"
    except Exception:
        pass
        
    try:
        # Simple query to check postgres
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
