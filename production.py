import os
import re
from pathlib import Path
from secrets import compare_digest, token_urlsafe

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles

from app import app as api_app, lifespan


frontend_dist = Path(__file__).resolve().parent / "frontend" / "dist"
demo_password = os.getenv("DEMO_PASSWORD", "")
on_render = os.getenv("RENDER") == "true"
public_demo = os.getenv("PUBLIC_DEMO") == "true"
visitor_cookie = "__Host-woo_demo_visitor" if on_render else "woo_demo_visitor"
visitor_token = re.compile(r"[A-Za-z0-9_-]{43}")

if on_render and not public_demo and not demo_password:
    raise RuntimeError("Set DEMO_PASSWORD before starting the hosted app.")
if public_demo and not (os.getenv("PUBLIC_DEMO_GEMINI_API_KEY") and os.getenv("GEMINI_MODEL")):
    raise RuntimeError("Set PUBLIC_DEMO_GEMINI_API_KEY and GEMINI_MODEL for the public demo.")

app = FastAPI(lifespan=lifespan, openapi_url=None)
basic_auth = HTTPBasic(auto_error=False)


@app.middleware("http")
async def protect_demo(request: Request, call_next):
    if request.method == "GET" and request.url.path == "/api/health":
        return await call_next(request)

    if public_demo:
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        visitor_id = request.cookies.get(visitor_cookie, "")
        new_visitor = visitor_token.fullmatch(visitor_id) is None
        if new_visitor:
            visitor_id = token_urlsafe(32)
        request.state.demo_visitor_id = visitor_id

        response = await call_next(request)
        response.headers["Cache-Control"] = "private, no-store"
        if new_visitor:
            response.set_cookie(
                visitor_cookie, visitor_id, max_age=86400, httponly=True,
                secure=on_render or request.url.scheme == "https", samesite="lax",
            )
        return response

    if not demo_password:
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
