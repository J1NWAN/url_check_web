from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from .auth_model import UserCreate, UserResponse
from .auth_service import create_user
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(
    prefix="/api/auth",
    tags=["인증"],
    responses={404: {"description": "찾을 수 없음"}},
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    새로운 사용자 회원가입 엔드포인트.
    
    - **email**: 유효한 이메일 주소 (필수)
    - **password**: 8자 이상의 암호, 대소문자, 숫자, 특수문자 포함 (필수)
    - **username**: 사용자 이름 (선택 사항)
    
    성공 시 생성된 사용자 정보를 반환합니다(비밀번호 제외).
    """
    try:
        user = await create_user(user_data)
        return user
    except HTTPException as e:
        # HTTPException은 그대로 전파
        raise e
    except Exception as e:
        logger.exception(f"회원가입 처리 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 처리 중 오류가 발생했습니다."
        ) 