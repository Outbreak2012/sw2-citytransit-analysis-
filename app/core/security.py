from datetime import datetime, timedelta
from typing import Optional
import base64
from jose import JWTError, jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security = HTTPBearer()


def get_jwt_secret() -> str:
    """Get JWT secret, decoding from base64 if needed"""
    try:
        # Try to decode from base64 (Java backend uses base64 encoded secret)
        return base64.b64decode(settings.JWT_SECRET).decode('utf-8')
    except:
        # If not base64, return as is
        return settings.JWT_SECRET


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_jwt_secret(), algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    
    # En modo desarrollo, permitir acceso si el token falla
    try:
        payload = decode_token(token)
        user_email: str = payload.get("sub")
        if user_email is None:
            if settings.DEBUG:
                return {"email": "dev@citytransit.com", "payload": {"sub": "dev@citytransit.com", "dev_mode": True}}
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {"email": user_email, "payload": payload}
    except HTTPException:
        if settings.DEBUG:
            return {"email": "dev@citytransit.com", "payload": {"sub": "dev@citytransit.com", "dev_mode": True}}
        raise


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(lambda: None)):
    """Get current authenticated user from JWT token (optional for development)"""
    if credentials is None:
        # Return mock user for development/testing
        return {"email": "dev@test.com", "payload": {"sub": "dev@test.com", "dev_mode": True}}
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_email: str = payload.get("sub")
        if user_email is None:
            return {"email": "dev@test.com", "payload": {"sub": "dev@test.com", "dev_mode": True}}
        return {"email": user_email, "payload": payload}
    except:
        # If token validation fails, return mock user
        return {"email": "dev@test.com", "payload": {"sub": "dev@test.com", "dev_mode": True}}
