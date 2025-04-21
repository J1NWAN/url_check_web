from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Menu(BaseModel):
    """메뉴 정보 모델"""
    name: str = Field(..., description="메뉴명")
    path: str = Field(..., description="URL 경로")
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class SystemBase(BaseModel):
    """시스템 기본 정보 모델"""
    eng_name: str = Field(..., description="시스템 영문명")
    kor_name: str = Field(..., description="시스템 한글명")
    url: str = Field(..., description="시스템 URL(도메인)")
    menus: List[Menu] = Field(default=[], description="메뉴 목록")
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class SystemCreate(SystemBase):
    """시스템 생성 모델"""
    created_at: datetime = Field(default_factory=datetime.now, description="생성일")
    created_by: str = Field(..., description="생성자 ID")
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class SystemUpdate(BaseModel):
    """시스템 수정 모델"""
    eng_name: Optional[str] = None
    kor_name: Optional[str] = None
    url: Optional[str] = None
    menus: Optional[List[Menu]] = None
    updated_at: datetime = Field(default_factory=datetime.now, description="수정일")
    updated_by: str = Field(..., description="수정자 ID")
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class SystemResponse(SystemBase):
    """시스템 응답 모델"""
    id: str = Field(..., description="시스템 ID")
    created_at: datetime = Field(..., description="생성일")
    created_by: str = Field(..., description="생성자 ID")
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
