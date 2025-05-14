from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
import re

class ProfileUpdate(BaseModel):
    """프로필 업데이트 요청 모델"""
    email: EmailStr = Field(..., description="사용자 이메일 주소")
    phone: Optional[str] = Field(None, description="사용자 휴대폰번호")
    bio: Optional[str] = Field(None, description="자기소개")
    new_password: Optional[str] = Field(None, min_length=8, max_length=20, description="새 비밀번호")
    profile_color: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        """휴대폰번호 형식 검증"""
        if v is not None and not re.match(r'^01[016789]-?\d{3,4}-?\d{4}$', v):
            raise ValueError('유효한 휴대폰번호 형식이 아닙니다')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        """비밀번호 검증"""
        if v is not None:
            if len(v) < 8 or len(v) > 20:
                raise ValueError('비밀번호는 8~20자 사이여야 합니다')
        return v

class ProfileResponse(BaseModel):
    """프로필 응답 모델"""
    id: str
    userid: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    bio: Optional[str] = None
    profile_color: Optional[str] = None

class AdminUserResponse(BaseModel):
    """관리자 사용자 응답 모델"""
    id: str
    userid: str
    name: str
    email: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    profile_color: Optional[str] = None
    role: Optional[str] = "user"

class AdminListResponse(BaseModel):
    """관리자 목록 응답 모델"""
    admins: List[AdminUserResponse]

class AdminDetailRequest(BaseModel):
    """관리자 상세 정보 요청 모델"""
    admin_id: str

class AdminUpdateRequest(BaseModel):
    """관리자 정보 업데이트 요청 모델"""
    email: EmailStr = Field(..., description="사용자 이메일 주소")
    phone: Optional[str] = Field(None, description="사용자 휴대폰번호")
    bio: Optional[str] = Field(None, description="자기소개")
    new_password: Optional[str] = Field(None, min_length=8, max_length=20, description="새 비밀번호")
    profile_color: Optional[str] = None
    role: Optional[str] = Field(None, description="사용자 권한 (user, admin, super-admin)")
    
    @validator('phone')
    def validate_phone(cls, v):
        """휴대폰번호 형식 검증"""
        if v is not None and not re.match(r'^01[016789]-?\d{3,4}-?\d{4}$', v):
            raise ValueError('유효한 휴대폰번호 형식이 아닙니다')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        """비밀번호 검증"""
        if v is not None:
            if len(v) < 8 or len(v) > 20:
                raise ValueError('비밀번호는 8~20자 사이여야 합니다')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        """권한 검증"""
        if v is not None and v not in ["", "user", "admin", "super-admin"]:
            raise ValueError('유효한 권한이 아닙니다. 권한 없음, user, admin, super-admin 중 하나여야 합니다.')
        return v
