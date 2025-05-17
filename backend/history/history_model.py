from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class InspectionResult(BaseModel):
    """개별 메뉴(URL) 점검 결과"""
    url: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    is_error: bool = False
    inspection_date: datetime = Field(default_factory=datetime.now)

class InspectionHistory(BaseModel):
    """시스템의 점검 이력"""
    id: Optional[str] = None
    system_id: str
    system_name: str
    inspection_date: datetime = Field(default_factory=datetime.now)
    results: List[InspectionResult] = []
    has_error: bool = False
    summary: Optional[Dict[str, Any]] = None

class LatestInspectionResult(BaseModel):
    """시스템의 최신 점검 결과"""
    inspection_date: Optional[datetime] = None
    has_error: bool = False

class SystemStatistics(BaseModel):
    """시스템 점검 결과 통계"""
    total_inspections: int = 0
    success_count: int = 0
    error_count: int = 0
    success_rate: float = 0.0

class SystemInspectionSummary(BaseModel):
    """시스템 점검 요약 정보"""
    system_id: str
    system_name: str
    latest_result: Optional[LatestInspectionResult] = None
    statistics: Optional[SystemStatistics] = None

class InspectionHistorySummary(BaseModel):
    """전체 시스템 점검 이력 요약"""
    systems: List[SystemInspectionSummary] = []
