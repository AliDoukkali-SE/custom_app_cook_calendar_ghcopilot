from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import router as meals_router, shopping_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(meals_router)
app.include_router(shopping_router)


@app.get("/")
async def read_root():
    return FileResponse("static/index.html")


@app.get("/health")
async def read_health():
    return {"status": "ok"}


@app.get("/api/me")
async def read_me(request: Request):
    """Return the signed-in user identity injected by Azure Container Apps Easy Auth.

    When running behind Easy Auth, every request carries the principal headers below.
    Locally (or when auth is disabled) the headers are absent and we return an anonymous payload.
    """
    name = request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME")
    oid = request.headers.get("X-MS-CLIENT-PRINCIPAL-ID")
    idp = request.headers.get("X-MS-CLIENT-PRINCIPAL-IDP")
    return {
        "authenticated": bool(name),
        "name": name,
        "id": oid,
        "provider": idp,
    }
