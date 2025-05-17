from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from util.util import verify_token
import logging
from config.templates import templates
from typing import Optional, List
from .history_service import get_inspection_history_summary, get_system_inspection_history
from .history_model import InspectionHistorySummary, InspectionHistory

# 로거 설정
logger = logging.getLogger(__name__)

# 토큰 인증 의존성
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# 라우터 정의
router = APIRouter(tags=["점검 이력"])

######################################################## 템플릿 반환 라우터 ########################################################
# 점검 이력 목록 화면
@router.get("/admin/history", tags=["점검 이력 목록 화면"])
async def history_list_page(request: Request):
    return templates.TemplateResponse("admin/history.html", {"request": request})

# 점검 이력 상세 화면
@router.get("/admin/history/detail", tags=["점검 이력 상세 화면"])
async def history_detail_page(request: Request, system_id: Optional[str] = None):
    return templates.TemplateResponse("admin/history_detail.html", {"request": request, "system_id": system_id})

######################################################## API 라우터 ########################################################
# 점검 이력 요약 정보 API
@router.get("/api/inspection/history/summary", response_model=InspectionHistorySummary, tags=["점검 이력 API"])
async def get_inspection_summary(token: str = Depends(oauth2_scheme)):
    """시스템별 점검 이력 요약 정보를 반환합니다."""
    try:
        # 토큰 검증
        try:
            # verify_token은 (user_id, payload) 튜플을 반환하는 비동기 함수
            user_id, payload = await verify_token(token)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 유효하지 않습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 점검 이력 요약 정보 가져오기
        summary = await get_inspection_history_summary()
        
        # 디버깅 로그 추가
        logger.info(f"점검 이력 요약 정보 조회 성공: {summary}")
        
        return summary
    
    except HTTPException as e:
        # HTTP 예외는 그대로 전달
        raise e
    except Exception as e:
        logger.error(f"점검 이력 요약 정보 API 오류: {str(e)}")
        # 디버깅을 위한 더 자세한 오류 메시지 추가
        import traceback
        logger.error(f"상세 오류 내용: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 오류: {str(e)}"
        )

# 시스템별 상세 점검 이력 API
@router.get("/api/inspection/history/{system_id}", tags=["점검 이력 API"])
async def get_system_history(system_id: str, token: str = Depends(oauth2_scheme)):
    """특정 시스템의 상세 점검 이력을 반환합니다."""
    try:
        # 토큰 검증
        try:
            # verify_token은 (user_id, payload) 튜플을 반환하는 비동기 함수
            user_id, payload = await verify_token(token)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 유효하지 않습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 시스템 ID 검증
        if not system_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="시스템 ID가 필요합니다"
            )
        
        # 시스템별 점검 이력 가져오기
        history_list = await get_system_inspection_history(system_id)
        
        return {"history": history_list}
    except HTTPException as e:
        # HTTP 예외는 그대로 전달
        raise e
    except Exception as e:
        logger.error(f"시스템별 점검 이력 API 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 오류: {str(e)}"
        )