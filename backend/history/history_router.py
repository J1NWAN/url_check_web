from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from util.util import verify_token
import logging
from config.templates import templates

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(tags=["점검 이력"])

######################################################## 템플릿 반환 라우터 ########################################################
# 로그인 화면
@router.get("/admin/history", tags=["점검 이력 목록 화면"])
async def history_list_page(request: Request):
    return templates.TemplateResponse("admin/history.html", {"request": request})