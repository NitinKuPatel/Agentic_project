from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.infrastructure.db.mongo import db
from app.infrastructure.cache.redis_client import redis_client
from app.api.routes import health, query, ingest, auth, history

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.observability.logging import logger
    logger.info("Application starting up...")
    
    # Startup
    db.connect()
    logger.info("Infrastructure initialized")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")
    db.close()
    await redis_client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth.router, prefix=settings.API_V1_STR + "/auth", tags=["Auth"])
app.include_router(query.router, prefix=settings.API_V1_STR, tags=["Query"])
app.include_router(ingest.router, prefix=settings.API_V1_STR, tags=["Ingestion"])
app.include_router(history.router, prefix=settings.API_V1_STR, tags=["History (Admin & User)"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
