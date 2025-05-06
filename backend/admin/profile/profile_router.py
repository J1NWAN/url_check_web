from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import logging
from config.templates import templates
from .profile_model import ProfileUpdate, ProfileResponse
from .profile_service import update_profile
from util.util import verify_token

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(tags=["프로필"])

# 프로필 페이지
@router.get("/admin/profile")
async def admin_profile(request: Request):
    return templates.TemplateResponse("admin/profile.html", {"request": request})

# 프로필 업데이트 API
@router.put("/api/profile/update", response_model=ProfileResponse, tags=["프로필 API"])
async def update_user_profile(profile_data: ProfileUpdate, user_id_and_payload = Depends(verify_token)):
    """
    사용자 프로필 정보를 업데이트하는 엔드포인트.
    
    - **email**: 이메일 주소 (필수)
    - **phone**: 휴대폰번호 (선택)
    - **bio**: 자기소개 (선택)
    - **new_password**: 새 비밀번호 (선택, 8~20자)
    
    JWT 토큰 인증이 필요합니다(Authorization 헤더에 Bearer 토큰 포함).
    
    성공 시 업데이트된 사용자 프로필 정보를 반환합니다.
    """
    try:
        user_id, _ = user_id_and_payload
        updated_profile = await update_profile(user_id, profile_data)
        return updated_profile
    except HTTPException as e:
        # HTTPException은 그대로 전파
        raise e
    except Exception as e:
        logger.exception(f"프로필 업데이트 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프로필 업데이트 중 오류가 발생했습니다."
        )