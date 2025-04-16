from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter()

templates = Jinja2Templates(directory="frontend/view/admin")

# API 전용 : JSON 반환
@router.get("/api/dashboard", status_code=status.HTTP_201_CREATED)
async def dashboard_json_data():
    try:
        return ''
    except HTTPException as e:
        # HTTPException은 그대로 전파
        raise e
    except Exception as e:
        logger.exception(f"회원가입 처리 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 처리 중 오류가 발생했습니다."
        )

# API 전용 : JSON 반환
@router.get("/admin/dashboard", status_code=status.HTTP_201_CREATED)
async def dashboard_view():
    return templates.TemplateResponse("dashboard.html")