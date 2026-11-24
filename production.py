import os
from pathlib import Path
from secrets import compare_digest

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles

from app import app as api_app, lifespan


frontend_dist = Path(__file__).resolve().parent / "frontend" / "dist"
demo_password = os.getenv("DEMO_PASSWORD", "")

if os.getenv("RENDER") == "true" and not demo_password:
    raise RuntimeError("Set DEMO_PASSWORD before starting the hosted app.")

app = FastAPI(lifespan=lifespan, openapi_url=None)
basic_auth = HTTPBasic(auto_error=False)


@app.middleware("http")
async def require_demo_login(request: Request, call_next):
    if not demo_password or (
        request.method == "GET" and request.url.path == "/api/health"
    ):
        return await call_next(request)

    try:
        credentials = await basic_auth(request)
    except HTTPException:
        credentials = None

    if (
        credentials is not None
        and credentials.username == "demo"
        and compare_digest(credentials.password.encode(), demo_password.encode())
    ):
        return await call_next(request)

    return Response(
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="WooCommerce Demo"'},
    )


app.mount("/api", api_app)
app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")