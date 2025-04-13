import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Firebase 서비스 계정 키 파일 경로 (직접 수정 필요)
CRED_PATH = "path/to/your/serviceAccountKey.json"

# Firebase 초기화
'''
try:
    cred = credentials.Certificate(CRED_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firestore initialized successfully")
except Exception as e:
    print(f"Error initializing Firestore: {e}")
    db = None
'''

app = FastAPI(
    title="URL Check Web API",
    description="URL 확인 및 사용자 관리를 위한 FastAPI 기반 백엔드",
    version="0.1.0"
)

# CORS 미들웨어 설정 추가
origins = [
    "http://localhost",         # 일반적인 로컬 개발 환경
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

# 여기에 API 엔드포인트 추가
from api.auth.auth_router import router as auth_router

# 라우터 등록 (접두사 없이 직접 등록)
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "URL Check Web API에 오신 것을 환영합니다!"}

# 여기에 API 엔드포인트 추가


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 