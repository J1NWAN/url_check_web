from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import logging
from config.templates import templates

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(tags=["프로필"])

# 프로필 페이지
@router.get("/admin/profile")
async def admin_profile(request: Request):
    return templates.TemplateResponse("admin/profile.html", {"request": request})