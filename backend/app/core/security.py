from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

# Password hashing - bcrypt is the gold standard

# OAuth2 scheme - reads token from Authorization: Bearer <token>
from fastapi.security import HTTPBearer
oauth2_scheme = HTTPBearer()

# Password helpers

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain[:72].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain[:72].encode("utf-8"), hashed.encode("utf-8"))


# Token creation

def create_access_token(user_id:str)-> str:
    expire = datetime.now(timezone.utc)+(timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub":user_id,"type":"access", "exp":expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(user_id:str)->str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {"sub": user_id, "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# TOKEN VERIFICATION

def decode_token(token:str, expected_type:str = "access") -> Optional[str]:

    """
    Decodes a JWT and returns the user_id(sub claim).
    Returns None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload.get("sub")
    except JWTError:
        return None
    

# FastAPI dependencies

def get_current_user(
    credentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db),
):
    from app.models.users import User
    token = credentials.credentials
    
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_token(token, expected_type="access")
    if not user_id:
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise credentials_error
    return user