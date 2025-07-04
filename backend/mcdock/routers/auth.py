from fastapi import APIRouter, Security

from .security import login_body, UNAUTHORIZED
from .models import ResponseMessage, TokenResponse


router = APIRouter(prefix="/auth")


@router.post("/login", response_model=TokenResponse, responses=UNAUTHORIZED)
async def login(creds = Security(login_body)):
    return creds

@router.post("/logout", response_model=ResponseMessage)
async def logout():
    return ResponseMessage(message="Bye!")