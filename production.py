from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import app as api_app, lifespan


frontend_dist = Path(__file__).resolve().parent / "frontend" / "dist"

app = FastAPI(lifespan=lifespan, openapi_url=None)
app.mount("/api", api_app)
app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")