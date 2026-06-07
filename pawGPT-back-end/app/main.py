from app.routes import auth_router
from app.config import DATABASE_URL
from app.routes import query_router
from contextlib import asynccontextmanager
from fastapi import FastAPI

import asyncpg

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await asyncpg.create_pool(DATABASE_URL)
    yield
    await app.state.db_pool.close()

app = FastAPI(title="PawGPT backend", lifespan=lifespan)

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication Framework"]
)

app.include_router(
    query_router,
    prefix="/api/v1/query",
    tags=["RAG Core engine"]
)