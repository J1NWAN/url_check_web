from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import logging
from config.templates import templates

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(tags=["시스템"])

# 시스템 페이지
@router.get("/admin/system")
async def admin_system(request: Request):
    return templates.TemplateResponse("admin/system.html", {"request": request})