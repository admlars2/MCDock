import bcrypt
from datetime import datetime, UTC
from typing import Annotated

from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import WebSocket, WebSocketDisconnect
from jose import jwt, JWTError

from ..core.config import settings
from .models import LoginBody, TokenResponse


# ─────────────────────────── responses ───────────────────────────
UNAUTHORIZED = {401: {"description": "Unauthorized"}}

# ─────────────────────────── helpers ────────────────────────────
_HASH_BYTES = settings.PASSWORD_HASH.encode()

bearer_scheme = HTTPBearer(auto_error=False)

def _verify_password(raw: str) -> bool:
    if not _HASH_BYTES:
        return False
    return bcrypt.checkpw(raw.encode(), _HASH_BYTES)

def _create_token() -> str:
    exp = datetime.now(UTC) + settings.JWT_TTL   # aware datetime
    payload = {"sub": settings.USER, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.HASH_ALGO)

# ─────────────────────────── dependencies ────────────────────────
def login_body(body: LoginBody) -> TokenResponse:
    if body and body.username == settings.USER and _verify_password(body.password):
        return TokenResponse(token=_create_token(), user=settings.USER)
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

def require_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)]
):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.HASH_ALGO],
        )
        if payload.get("sub") != settings.USER:
            raise JWTError()
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
async def require_ws_user(ws: WebSocket) -> None:
    """
    Validate JWT for a WebSocket connection.

    Order of precedence:
    1. Authorization: Bearer <token> header  (non-browser clients / tests)
    2. ?token=<jwt> query parameter          (browser clients)
    """
    # 1️⃣ try header first
    header = ws.headers.get("authorization")
    token  = None
    if header and header.lower().startswith("bearer "):
        token = header.split(" ", 1)[1]

    # 2️⃣ fall back to ?token=
    if not token:
        token = ws.query_params.get("token")

    if not token:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)  # 4403
        raise WebSocketDisconnect

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.HASH_ALGO],  # e.g. "HS256"
        )
        if payload.get("sub") != settings.USER:
            raise JWTError()
    except JWTError:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketDisconnect