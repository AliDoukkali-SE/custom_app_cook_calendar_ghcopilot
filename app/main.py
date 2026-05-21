from __future__ import annotations

from fastapi import FastAPI
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
