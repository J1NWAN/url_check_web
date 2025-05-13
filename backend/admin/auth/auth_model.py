from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

class UserCreate(BaseModel):
    userid: str = Field(..., min_length=4, max_length=20, description="사용자 아이디 (4-20자)")
    name: str = Field(..., min_length=2, max_length=50, description="사용자 이름")
    email: EmailStr = Field(..., description="사용자 이메일 주소")
    password: str = Field(..., min_length=8, description="사용자 비밀번호(최소 8자)")
    password_confirm: str = Field(..., description="비밀번호 확인")
    
    @validator('userid')
    def userid_format(cls, v):
        """아이디 형식 검증"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('아이디는 영문자, 숫자, 밑줄(_)만 포함할 수 있습니다')
        return v
        
    @validator('password')
    def password_strength(cls, v):
        """비밀번호 강도 검증"""
        if not re.search(r'[a-z]', v):
            raise ValueError('비밀번호에는 최소 하나의 소문자가 포함되어야 합니다')
        if not re.search(r'[0-9]', v):
            raise ValueError('비밀번호에는 최소 하나의 숫자가 포함되어야 합니다')
        return v
    
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        """비밀번호 일치 여부 검증"""
        if 'password' in values and v != values['password']:
            raise ValueError('비밀번호가 일치하지 않습니다')
        return v

class UserResponse(BaseModel):
    id: str
    userid: str
    name: str
    email: EmailStr

class UserLogin(BaseModel):
    userid: str = Field(..., min_length=4, description="사용자 아이디")
    password: str = Field(..., min_length=8, description="사용자 비밀번호")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    userid: str
    name: str

class CurrentUser(BaseModel):
    id: str
    userid: str
    name: str
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    created_at: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    profile_color: Optional[str] = None 