from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.indoor import router as indoor_router
from app.api.outdoor import router as outdoor_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.polling.service import build_default_poller
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from starlette.exceptions import HTTPException

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    poller = None
    if settings.enable_poller:
        poller = build_default_poller()
        poller.start()
    try:
        yield
    finally:
        if poller is not None:
            await poller.stop()

app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.include_router(health_router)
app.include_router(indoor_router)
app.include_router(outdoor_router)

#Support for serving static React Frontend 
LOCAL_NAT_REGEX = (
    r"^https?://("
    r"localhost|127(?:\.\d{1,3}){3}|0\.0\.0\.0|"
    r"10(?:\.\d{1,3}){3}|"
    r"192\.168(?:\.\d{1,3}){2}|"
    r"172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2}"
    r")(?::\d{1,5})?$"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_origin_regex=LOCAL_NAT_REGEX,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
ASSETS_DIR = DIST_DIR / "assets"

@app.get("/", include_in_schema=False)
def root_index():
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "status": "running",
        "message": "Backend is up. UI build not found. Build the frontend or use the included dist folder.",
        "openapi": "/docs",
    }

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

favicon_candidates = [DIST_DIR / "favicon.svg", BASE_DIR / "public" / "favicon.svg"]

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    for candidate in favicon_candidates:
        if candidate.exists():
            return FileResponse(candidate)
    raise HTTPException(status_code=404, detail="favicon not found")