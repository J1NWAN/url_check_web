import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore

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

app = FastAPI()

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

@app.get("/")
async def root():
    return {"message": "Hello World"}

# 여기에 API 엔드포인트 추가


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 