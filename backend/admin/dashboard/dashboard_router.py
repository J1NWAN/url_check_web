from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import logging
from config.templates import templates
from .dashboard_service import get_dashboard_statistics

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(tags=["대시보드"])

# 관리자 페이지
@router.get("/admin/dashboard")
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

# 대시보드 통계 API
@router.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """대시보드에 표시할 통계 정보를 반환하는 API"""
    try:
        # 서비스 함수 호출하여 통계 정보 가져오기
        return await get_dashboard_statistics()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"대시보드 통계 API 호출 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대시보드 통계 API 호출 중 오류가 발생했습니다: {str(e)}"
        )