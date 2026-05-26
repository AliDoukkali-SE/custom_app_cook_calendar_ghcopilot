from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .auth import SESSION_SECRET, get_current_user, router as auth_router
from .routes import router as meals_router, shopping_router

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    https_only=True,
    same_site="lax",
    max_age=60 * 60,  # 1 hour
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_router)
app.include_router(meals_router, dependencies=[Depends(get_current_user)])
app.include_router(shopping_router, dependencies=[Depends(get_current_user)])


@app.get("/login")
async def login_page():
    return FileResponse("static/login.html")


@app.get("/")
async def read_root(request: Request):
    if not request.session.get("user"):
        return RedirectResponse("/login")
    return FileResponse("static/index.html")


@app.get("/health")
async def read_health():
    return {"status": "ok"}
