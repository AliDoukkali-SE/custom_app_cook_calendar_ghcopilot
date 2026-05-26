from __future__ import annotations

import os
import urllib.parse

import msal
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
SESSION_SECRET = os.getenv("SECRET_KEY", "change-me-in-production")

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
        error_msg = result.get("error_description", "Invalid credentials.")
        return RedirectResponse(
            f"/login?error={urllib.parse.quote(error_msg)}",
            status_code=303,
        )

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
