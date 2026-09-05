from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

from app.core.config import settings


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )


def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[ALGORITHM],
        )

        username = payload.get("sub")

        if not username:
            return None

        return username

    except Exception:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    username = verify_token(credentials.credentials)

    if username is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
        )

    return username