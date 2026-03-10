from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.proxy.request_models import HealthResponse
from src.utils.config import settings
from src.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard-ui"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("aegis.starting", version="0.1.0")

    from src.storage.database import init_db
    await init_db()

    from src.storage.migrations import run_migrations
    await run_migrations()

    from src.embeddings.encoder import get_encoder
    get_encoder()

    from src.cache.redis_client import get_redis
    await get_redis()

    logger.info("aegis.ready")
    yield

    from src.cache.redis_client import close_redis
    await close_redis()
    logger.info("aegis.shutdown")


app = FastAPI(
    title="Aegis",
    description="Real-Time Hallucination Detection & Containment Firewall for LLM Applications",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy")


@app.get("/ready", response_model=HealthResponse)
async def ready():
    return HealthResponse(status="ready")


@app.get("/dashboard")
async def dashboard():
    return FileResponse(DASHBOARD_DIR / "index.html")


from src.proxy.router import router as proxy_router
app.include_router(proxy_router, prefix="/v1")

from src.dashboard.api import router as dashboard_router
app.include_router(dashboard_router, prefix="/v1/dashboard")

if DASHBOARD_DIR.exists():
    app.mount("/dashboard-ui", StaticFiles(directory=str(DASHBOARD_DIR)), name="dashboard-ui")
