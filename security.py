import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config import settings
from database import get_database_session
from models import UserAccount

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def hash_user_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

def verify_user_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_signed_access_token(user_identifier: str) -> str:
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_identifier,
        "type": "access",
        "exp": expire_time
    }
    return jwt.encode(payload, settings.security_secret_key, algorithm=settings.security_algorithm_name)

def create_signed_refresh_token(user_identifier: str) -> str:
    expire_time = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": user_identifier,
        "type": "refresh",
        "exp": expire_time
    }
    return jwt.encode(payload, settings.security_secret_key, algorithm=settings.security_algorithm_name)

def decode_and_verify_token(token: str, expected_type: str = "access") -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.security_secret_key, algorithms=[settings.security_algorithm_name])
        token_type = payload.get("type", "access")
        if token_type != expected_type:
            return None
        return payload
    except Exception:
        return None

async def get_authenticated_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    database_session: AsyncSession = Depends(get_database_session)
) -> UserAccount:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    resolved_token = token or request.cookies.get("access_token")
    if not resolved_token:
        raise unauthorized

    payload = decode_and_verify_token(resolved_token, expected_type="access")
    if not payload:
        raise unauthorized

    username = payload.get("sub")
    if not username:
        raise unauthorized

    query = select(UserAccount).where(UserAccount.username == username)
    result = await database_session.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise unauthorized

    return user

async def get_optional_authenticated_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    database_session: AsyncSession = Depends(get_database_session)
) -> Optional[UserAccount]:
    resolved_token = token or request.cookies.get("access_token")
    if not resolved_token:
        return None

    payload = decode_and_verify_token(resolved_token, expected_type="access")
    if not payload:
        return None

    username = payload.get("sub")
    if not username:
        return None

    query = select(UserAccount).where(UserAccount.username == username)
    result = await database_session.execute(query)
    return result.scalar_one_or_none()
