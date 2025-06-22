from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings

bearer_scheme = HTTPBearer(auto_error=False)

def require_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
) -> None:
    """
    Reject the request unless a valid static Bearer token is supplied.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Missing bearer token")
    if credentials.credentials != settings.CONTROL_PANEL_BEARER_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid bearer token")