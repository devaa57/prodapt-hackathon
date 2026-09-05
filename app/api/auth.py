from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest):
    """
    Authenticate against the hardcoded demo credentials in the configuration.
    """
    if (
        credentials.username != settings.demo_username
        or credentials.password != settings.demo_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(credentials.username)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
