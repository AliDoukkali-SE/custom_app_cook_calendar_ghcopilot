from __future__ import annotations

import logging
import os
import secrets

import msal
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)

AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")


def _resolve_session_secret() -> str:
    """Return the session signing secret.

    - If SECRET_KEY is set, use it.
    - If it is missing AND Entra ID is configured (real deployment),
      raise: signing sessions with a known default would let anyone
      forge a cookie and impersonate any user.
    - Otherwise (local dev / tests), generate an ephemeral random key
      and warn. Sessions will be invalidated on restart.
    """
    value = os.getenv("SECRET_KEY")
    if value:
        return value
    if AZURE_CLIENT_ID and AZURE_TENANT_ID:
        raise RuntimeError(
            "SECRET_KEY env var is required when Azure Entra ID is configured. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    logger.warning(
        "SECRET_KEY not set; generating an ephemeral key. "
        "Sessions will be invalidated on every restart. "
        "Set SECRET_KEY in production."
    )
    return secrets.token_urlsafe(32)


SESSION_SECRET = _resolve_session_secret()

AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
SCOPES = ["User.Read"]


def _build_msal_app() -> msal.PublicClientApplication:
    return msal.PublicClientApplication(
        AZURE_CLIENT_ID,
        authority=AUTHORITY,
    )


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Authenticate the user via Azure Entra ID (ROPC flow)."""
    if not AZURE_CLIENT_ID or not AZURE_TENANT_ID:
        raise HTTPException(
            status_code=503,
            detail=(
                "Azure Entra ID is not configured. "
                "Set AZURE_CLIENT_ID and AZURE_TENANT_ID."
            ),
        )

    msal_app = _build_msal_app()
    result = msal_app.acquire_token_by_username_password(
        username, password, scopes=SCOPES
    )

    if "error" in result:
        # Log the detail server-side; show a generic message to the user
        # to avoid leaking whether the account exists, requires MFA, etc.
        logger.warning(
            "Login failed for %s: %s - %s",
            username,
            result.get("error"),
            result.get("error_description"),
        )
        return RedirectResponse("/login?error=1", status_code=303)

    claims = result.get("id_token_claims") or {}
    request.session["user"] = {
        "oid": claims.get("oid"),
        "name": claims.get("name") or username,
        "email": username,
    }
    return RedirectResponse("/", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    """Clear the session and redirect to the login page."""
    request.session.clear()
    return RedirectResponse("/login")


@router.get("/me")
async def get_me(request: Request) -> dict:
    """Return the currently authenticated user's profile."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def get_current_user(request: Request) -> dict:
    """FastAPI dependency: return the authenticated user or raise 401."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
