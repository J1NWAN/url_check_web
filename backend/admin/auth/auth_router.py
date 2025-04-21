from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from .auth_model import UserCreate, UserResponse, UserLogin, Token, CurrentUser
from .auth_service import create_user, login_user, get_current_user
from util.util import verify_token
import logging
from config.templates import templates

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(tags=["인증"])

######################################################## 템플릿 반환 라우터 ########################################################
# 로그인 화면
@router.get("/auth/signin", tags=["로그인 화면"])
async def signin_page(request: Request):
    return templates.TemplateResponse("auth/signin.html", {"request": request})

# 회원가입 화면
@router.get("/auth/signup", tags=["회원가입 화면"])
async def signup_page(request: Request):
    return templates.TemplateResponse("auth/signup.html", {"request": request})

######################################################## API 라우터 ########################################################
# 회원가입 API
@router.post("/api/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["회원가입 API"])
async def register_user(user_data: UserCreate):
    """
    새로운 사용자 회원가입 엔드포인트.
    
    - **userid**: 사용자 아이디 (4-20자, 영문자, 숫자, 밑줄(_)만 허용) (필수)
    - **name**: 사용자 이름 (2-50자) (필수)
    - **email**: 유효한 이메일 주소 (필수)
    - **password**: 8자 이상의 암호, 대소문자, 숫자, 특수문자 포함 (필수)
    - **password_confirm**: 비밀번호 확인 (필수)
    
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

# 로그인 API
@router.post("/api/login", response_model=Token, tags=["로그인 API"])
async def login(login_data: UserLogin):
    """
    사용자 로그인 엔드포인트.
    
    - **userid**: 사용자 아이디 (필수)
    - **password**: 사용자 비밀번호 (필수)
    
    성공 시 액세스 토큰과 사용자 정보를 반환합니다.
    """
    try:
        token = await login_user(login_data)
        return token
    except HTTPException as e:
        # HTTPException은 그대로 전파
        raise e
    except Exception as e:
        logger.exception(f"로그인 처리 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다."
        )

# 현재 사용자 정보 조회 API
@router.get("/api/auth/me", response_model=CurrentUser, tags=["사용자 정보 API"])
async def get_me(user_id_and_payload = Depends(verify_token)):
    """
    현재 로그인한 사용자의 정보를 조회하는 엔드포인트.
    
    JWT 토큰 인증이 필요합니다(Authorization 헤더에 Bearer 토큰 포함).
    
    성공 시 현재 로그인한 사용자의 정보를 반환합니다.
    """
    try:
        user_id, _ = user_id_and_payload
        user = await get_current_user(user_id)
        return user
    except HTTPException as e:
        # HTTPException은 그대로 전파
        raise e
    except Exception as e:
        logger.exception(f"사용자 정보 조회 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 조회 중 오류가 발생했습니다."
        )