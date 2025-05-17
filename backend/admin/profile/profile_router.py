from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import logging
from config.templates import templates
from .profile_model import ProfileUpdate, ProfileResponse, AdminListResponse, AdminUserResponse, AdminUpdateRequest, AuthItem
from .profile_service import update_profile, get_admin_list, get_admin_detail, update_admin, get_user_auth
from util.util import verify_token
from config.database import get_db
from typing import Dict, Any

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(tags=["프로필"])

# 사용자 권한 가져오기 함수
async def get_user_role_from_token(payload: Dict[str, Any], user_id: str) -> str:
    """
    토큰 페이로드 또는 데이터베이스에서 사용자 권한을 가져옵니다.
    
    Args:
        payload: 토큰 페이로드
        user_id: 사용자 ID
        
    Returns:
        사용자 권한 (user, admin, super-admin)
        
    Raises:
        HTTPException: 데이터베이스 연결 오류 또는 사용자를 찾을 수 없는 경우
    """
    logger.info(f"토큰 페이로드: {payload}")
    
    # 토큰에서 auth 정보 확인
    if payload.get("auth"):
        # auth가 딕셔너리인 경우 (직접 토큰에 포함)
        if isinstance(payload.get("auth"), dict) and "role" in payload.get("auth"):
            role = payload.get("auth").get("role")
            logger.info(f"토큰에서 가져온 권한(auth dict): {role}")
            return role
        # auth가 리스트인 경우 (API 응답 형식)
        elif isinstance(payload.get("auth"), list) and len(payload.get("auth")) > 0:
            auth_item = payload.get("auth")[0]
            if isinstance(auth_item, dict) and "role" in auth_item:
                role = auth_item["role"]
                logger.info(f"토큰에서 가져온 권한(auth list): {role}")
                return role
    
    # 토큰에서 기존 role 정보 확인
    if payload.get("role"):
        role = payload.get("role")
        logger.info(f"토큰에서 가져온 권한(role): {role}")
        return role
    
    # 토큰에 권한 정보가 없으면 데이터베이스에서 조회
    logger.info("토큰에 권한 정보가 없어 데이터베이스에서 조회합니다.")
    return await get_user_auth(user_id)

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

# 관리자 목록 조회 API
@router.get("/api/admin/list", response_model=AdminListResponse, tags=["프로필 API"])
async def get_admin_users(user_id_and_payload = Depends(verify_token)):
    """
    시스템에 등록된 모든 관리자 목록을 조회하는 엔드포인트.
    자기 자신을 제외한 관리자 목록을 반환합니다.
    
    JWT 토큰 인증이 필요합니다(Authorization 헤더에 Bearer 토큰 포함).
    
    성공 시 관리자 목록을 반환합니다.
    """
    try:
        user_id, payload = user_id_and_payload
        
        # 토큰에서 권한 정보 확인 (없을 경우 데이터베이스에서 조회)
        role = await get_user_role_from_token(payload, user_id)
        
        admin_list = await get_admin_list(user_id)
        return admin_list
    except HTTPException as e:
        # HTTPException은 그대로 전파
        raise e
    except Exception as e:
        logger.exception(f"관리자 목록 조회 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 목록 조회 중 오류가 발생했습니다."
        )

# 특정 관리자 정보 조회 API
@router.get("/api/admin/{admin_id}", response_model=AdminUserResponse, tags=["프로필 API"])
async def get_admin_detail_by_id(admin_id: str, user_id_and_payload = Depends(verify_token)):
    """
    특정 관리자의 상세 정보를 조회하는 엔드포인트.
    
    Args:
        admin_id: 조회할 관리자 ID
    
    JWT 토큰 인증이 필요합니다(Authorization 헤더에 Bearer 토큰 포함).
    
    성공 시 관리자 상세 정보를 반환합니다.
    """
    try:
        user_id, payload = user_id_and_payload
        
        # 토큰에서 권한 정보 확인 (없을 경우 데이터베이스에서 조회)
        role = await get_user_role_from_token(payload, user_id)
        
        # 권한 확인 (admin 또는 super-admin만 조회 가능)
        if role not in ["admin", "super-admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="관리자 정보를 조회할 권한이 없습니다."
            )
        
        admin_detail = await get_admin_detail(admin_id)
        return admin_detail
    except HTTPException as e:
        # HTTPException은 그대로 전파
        raise e
    except Exception as e:
        logger.exception(f"관리자 정보 조회 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 정보 조회 중 오류가 발생했습니다."
        )

# 특정 관리자 정보 업데이트 API (PUT 메서드)
@router.put("/api/admin/{admin_id}", response_model=AdminUserResponse, tags=["프로필 API"])
@router.post("/api/admin/{admin_id}", response_model=AdminUserResponse, tags=["프로필 API"])
async def update_admin_by_id(admin_id: str, admin_data: AdminUpdateRequest, user_id_and_payload = Depends(verify_token)):
    """
    특정 관리자의 정보를 업데이트하는 엔드포인트.
    PUT 및 POST 메서드 모두 지원합니다.
    
    Args:
        admin_id: 업데이트할 관리자 ID
        admin_data: 업데이트할 관리자 정보
    
    JWT 토큰 인증이 필요합니다(Authorization 헤더에 Bearer 토큰 포함).
    
    성공 시 업데이트된 관리자 정보를 반환합니다.
    """
    try:
        user_id, payload = user_id_and_payload
        
        # 토큰에서 권한 정보 확인 (없을 경우 데이터베이스에서 조회)
        role = await get_user_role_from_token(payload, user_id)
        
        # super-admin 권한 확인
        if role != "super-admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="다른 관리자 정보를 수정할 권한이 없습니다."
            )
        
        updated_admin = await update_admin(admin_id, admin_data, user_id)
        return updated_admin
    except HTTPException as e:
        # HTTPException은 그대로 전파
        raise e
    except Exception as e:
        logger.exception(f"관리자 정보 업데이트 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 정보 업데이트 중 오류가 발생했습니다."
        )