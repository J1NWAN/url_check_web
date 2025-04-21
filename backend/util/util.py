from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from typing import Union, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# 비밀번호 암호화 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-for-jwt-needs-to-be-changed")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1일

# OAuth2 스키마 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def get_password_hash(password):
    """비밀번호를 해시화합니다."""
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """입력된 비밀번호와 해시된 비밀번호를 비교합니다."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: Dict[str, Any], expires_delta: Union[timedelta, None] = None):
    """사용자 인증을 위한 JWT 액세스 토큰을 생성합니다."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str = Depends(oauth2_scheme)):
    """
    JWT 토큰을 검증하고 사용자 ID를 추출합니다.
    
    Args:
        token: OAuth2 헤더로부터 받은 JWT 토큰
        
    Returns:
        tuple: (user_id, payload) - 사용자 ID와 토큰 페이로드
        
    Raises:
        HTTPException: 토큰이 유효하지 않거나 만료된 경우
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="토큰 인증에 실패했습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 토큰 디코딩
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # sub 필드에서 사용자 ID 추출
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        return user_id, payload
        
    except JWTError:
        raise credentials_exception 