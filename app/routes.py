from __future__ import annotations

# Backward-compatibility layer for legacy imports (app.routes).
from .dependencies import get_owner_id, get_store
from .routers import router

__all__ = ["router", "get_store", "get_owner_id"]
