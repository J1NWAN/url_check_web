import sys
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# config/database.py에서 Firestore 초기화를 처리하므로 여기서는 제거
from config.database import get_db

# 공통 템플릿 설정 모듈 임포트
from config.templates import mount_static_files

app = FastAPI(
    title="URL Check Web API",
    description="URL 확인 및 사용자 관리를 위한 FastAPI 기반 백엔드",
    version="0.1.0"
)

# 정적 파일 마운트
mount_static_files(app)

# CORS 미들웨어 설정 추가
origins = [
    "http://localhost",         # 일반적인 로컬 개발 환경
    "http://localhost:8000",    # FastAPI 기본 포트
    "http://localhost:8080",    # 다른 프론트엔드 개발 서버 포트 예시
    "http://127.0.0.1:5500",    # Live Server 기본 포트
    # 필요하다면 여기에 배포된 프론트엔드 주소 추가
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처 목록
    allow_credentials=True, # 자격 증명 허용 여부
    allow_methods=["*"],    # 모든 HTTP 메소드 허용
    allow_headers=["*"],    # 모든 HTTP 헤더 허용
)

# 인덱스 페이지 라우트
from fastapi import Request
from config.templates import templates

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 인증 라우터 등록
from admin.auth.auth_router import router as auth_router
app.include_router(auth_router)

# 대시보드 라우터 등록
from admin.dashboard.dashboard_router import router as dashboard_router
app.include_router(dashboard_router)

# 프로필 라우터 등록
from admin.profile.profile_router import router as profile_router
app.include_router(profile_router)

# 시스템 라우터 등록
from admin.system.system_router import router as system_router
app.include_router(system_router)

if __name__ == "__main__":
    # 시작 시 데이터베이스 연결 확인
    db = get_db()
    if db is None:
        logger.warning("Firestore 연결이 설정되지 않았습니다. 서비스 계정 키를 확인하세요.")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 