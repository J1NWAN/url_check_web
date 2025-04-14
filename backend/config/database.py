import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

# 서비스 계정 키 파일 경로 설정
# 1. 환경 변수에서 읽기 (권장)
# CRED_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# 2. 기본 경로 지정
CRED_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "key", "serviceAccountKey.json")

db = None
try:
    # 이미 초기화되었는지 확인
    if not firebase_admin._apps:
        if os.path.exists(CRED_PATH):
            cred = credentials.Certificate(CRED_PATH)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            logger.info("Firestore가 성공적으로 초기화되었습니다.")
        else:
            logger.warning(f"Firestore 인증 파일을 {CRED_PATH}에서 찾을 수 없습니다. "
                        f"serviceAccountKey.json 파일을 config/key 디렉토리에 넣어주세요.")
    else:
        # 이미 초기화된 앱에서 클라이언트 가져오기
        db = firestore.client()
        logger.info("Firestore가 이미 초기화되어 있습니다.")

except Exception as e:
    logger.error(f"Firestore 초기화 중 오류 발생: {e}")
    db = None

def get_db():
    """Firestore 클라이언트를 반환하는 함수"""
    if db is None:
        logger.warning("Firestore 클라이언트를 사용할 수 없습니다. 인증 정보를 확인하세요.")
    return db 