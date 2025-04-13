import firebase_admin
from firebase_admin import credentials, firestore
import os

# 환경 변수에서 서비스 계정 키 경로 읽기 (추천 방식)
# CRED_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") 
# 또는 직접 경로 지정 (경로 확인 필요)
CRED_PATH = "path/to/your/serviceAccountKey.json" # <--- 이 경로를 실제 키 파일 경로로 수정하세요!

db = None
try:
    # 이미 초기화되었는지 확인
    if not firebase_admin._apps:
        if CRED_PATH and os.path.exists(CRED_PATH):
            cred = credentials.Certificate(CRED_PATH)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("Firestore initialized successfully.")
        else:
            print(f"Warning: Firestore credential file not found at {CRED_PATH}. Firestore client will be None.")
    else:
        # 이미 초기화된 앱에서 클라이언트 가져오기
        db = firestore.client()
        print("Firestore already initialized.")

except Exception as e:
    print(f"Error initializing Firestore: {e}")
    db = None

def get_db():
    """Firestore 클라이언트를 반환하는 함수"""
    if db is None:
        print("Warning: Firestore client is not available.")
    return db 