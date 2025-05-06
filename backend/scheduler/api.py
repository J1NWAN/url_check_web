"""
URL Check Web 스케줄러 API 모듈

스케줄러 관리 및 수동 이메일 발송을 위한 API를 제공합니다.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Body, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 스케줄러 및 이메일 서비스 임포트
from .scheduler import get_scheduler, run_system_inspection
from .email_service import send_inspection_email
from admin.system.system_service import get_systems, perform_system_inspection

# 라우터 생성
router = APIRouter(tags=["scheduler"])

# 모델 정의
class EmailRequest(BaseModel):
    """이메일 발송 요청 모델"""
    recipients: List[EmailStr] = Field(..., description="수신자 이메일 목록")
    
    class Config:
        schema_extra = {
            "example": {
                "recipients": ["user1@example.com", "user2@example.com"]
            }
        }

class SchedulerStatus(BaseModel):
    """스케줄러 상태 응답 모델"""
    running: bool = Field(..., description="스케줄러 실행 상태")
    next_run_time: Optional[str] = Field(None, description="다음 실행 시간")
    jobs_count: int = Field(..., description="등록된 작업 수")
    
    class Config:
        schema_extra = {
            "example": {
                "running": True,
                "next_run_time": "2023-05-01T12:00:00",
                "jobs_count": 1
            }
        }

# API 엔드포인트
@router.get("/api/scheduler/status", response_model=SchedulerStatus)
async def get_scheduler_status():
    """
    스케줄러 상태를 조회합니다.
    """
    try:
        scheduler_instance = get_scheduler()
        
        if not scheduler_instance:
            return SchedulerStatus(
                running=False,
                next_run_time=None,
                jobs_count=0
            )
        
        # 시스템 점검 작업 정보 가져오기
        job = scheduler_instance.get_job('system_inspection')
        next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job and job.next_run_time else None
        
        return SchedulerStatus(
            running=scheduler_instance.running,
            next_run_time=next_run,
            jobs_count=len(scheduler_instance.get_jobs())
        )
    except Exception as e:
        logger.error(f"스케줄러 상태 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스케줄러 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/api/scheduler/run-inspection")
async def trigger_inspection():
    """
    시스템 점검 작업을 즉시 실행합니다.
    """
    try:
        await run_system_inspection()
        return {"message": "시스템 점검 작업이 실행되었습니다."}
    except Exception as e:
        logger.error(f"시스템 점검 작업 실행 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 점검 작업 실행 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/api/scheduler/send-email")
async def send_email(request: EmailRequest):
    """
    최신 점검 결과를 이메일로 발송합니다.
    """
    try:
        # 모든 시스템 목록 조회
        systems = await get_systems()
        
        if not systems:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="등록된 시스템이 없습니다."
            )
        
        # 각 시스템 점검 수행
        inspection_systems = []
        for system in systems:
            try:
                # 개별 시스템 점검 수행 (저장은 하지 않고 결과만 가져옴)
                inspection_data = await perform_system_inspection(system.id, "자동", "email_api", None)
                inspection_systems.append(inspection_data)
            except Exception as e:
                logger.error(f"시스템 점검 중 오류 발생 (ID: {system.id}): {str(e)}")
                continue
        
        if not inspection_systems:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="점검 결과를 생성할 수 없습니다."
            )
        
        # 이메일 발송
        success = await send_inspection_email(request.recipients, inspection_systems)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이메일 발송에 실패했습니다."
            )
        
        return {"message": f"{len(request.recipients)}명에게 이메일이 발송되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이메일 발송 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이메일 발송 중 오류가 발생했습니다: {str(e)}"
        ) 