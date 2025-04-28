from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
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

class InspectionMenuResult(BaseModel):
    """메뉴별 점검 결과 모델"""
    menu_name: str = Field(..., description="메뉴명")
    path: str = Field(..., description="URL 경로")
    status_code: int = Field(..., description="HTTP 상태 코드")
    status_text: str = Field(..., description="상태명(한글)")
    response_time: float = Field(..., description="응답 시간(ms)")
    headers: Dict[str, str] = Field(default={}, description="응답 헤더")
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class SystemInspection(BaseModel):
    """시스템 점검 이력 모델"""
    system_id: str = Field(..., description="시스템 ID")
    system_eng_name: str = Field(..., description="시스템 영문명")
    system_kor_name: str = Field(..., description="시스템 한글명")
    system_url: str = Field(..., description="시스템 URL")
    inspection_start: datetime = Field(..., description="점검 시작 시간")
    inspection_end: Optional[datetime] = Field(None, description="점검 종료 시간")
    inspection_results: List[InspectionMenuResult] = Field(default=[], description="메뉴별 점검 결과")
    inspection_type: str = Field(..., description="점검 유형(자동/수동)")
    created_by: str = Field(..., description="점검 생성자 ID")
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class SystemInspectionCreate(SystemInspection):
    """시스템 점검 이력 생성 모델"""
    pass

class SystemInspectionUpdate(BaseModel):
    """시스템 점검 이력 업데이트 모델"""
    inspection_end: Optional[datetime] = None
    inspection_results: Optional[List[InspectionMenuResult]] = None
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class SystemInspectionResponse(SystemInspection):
    """시스템 점검 이력 응답 모델"""
    id: str = Field(..., description="점검 이력 ID")
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
