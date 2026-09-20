"""FastAPI application initialization."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from clarity.api.routes import router
from clarity.db.session import init_db
from clarity.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is initialized on startup
    init_db()
    yield


app = FastAPI(
    title="Clarity Document Extraction API",
    description="Evidence-grade document extraction and investigation intelligence platform with pluggable VLM inference",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

from pathlib import Path
from fastapi.staticfiles import StaticFiles

app.include_router(router)

# Mount web frontend
web_dir = Path(__file__).parent.parent / "web"
web_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
