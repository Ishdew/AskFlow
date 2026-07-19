from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.arq_pool import init_arq_pool, close_arq_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_arq_pool()
    yield
    await close_arq_pool()


# Create the FastAPI app
# Schema is managed by Alembic migrations (see alembic/) — run `alembic upgrade head`
# before starting the app. There is no create_all-on-startup anymore.
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Should be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
