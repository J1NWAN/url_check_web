from util.util import get_password_hash
from config.database import get_db
from api.auth.auth_model import UserCreate, UserResponse
from fastapi import HTTPException, status
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_user(user_data: UserCreate) -> UserResponse:
    """
    새로운 사용자를 생성하고 Firestore에 저장합니다.
    
    Args:
        user_data: 사용자 등록 데이터 (아이디, 이름, 이메일, 비밀번호 등)
        
    Returns:
        생성된 사용자 정보 (비밀번호 제외)
        
    Raises:
        HTTPException: 데이터베이스 연결 오류, 아이디/이메일 중복, 또는 기타 오류 발생 시
    """
    # Firestore 데이터베이스 연결 가져오기
    db = get_db()
    if db is None:
        logger.error("데이터베이스 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 연결 오류가 발생했습니다."
        )

    # 사용자 컬렉션 참조
    users_ref = db.collection('user')
    
    # 아이디 중복 확인
    userid_query = users_ref.where('userid', '==', user_data.userid).limit(1).stream()
    if any(userid_query):
        logger.warning(f"이미 등록된 아이디로 가입 시도: {user_data.userid}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 아이디입니다."
        )
    
    # 이메일 중복 확인
    email_query = users_ref.where('email', '==', user_data.email).limit(1).stream()
    if any(email_query):
        logger.warning(f"이미 등록된 이메일로 가입 시도: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다."
        )

    # 비밀번호 해싱
    hashed_password = get_password_hash(user_data.password)
    
    # 사용자 데이터 준비 (비밀번호와 비밀번호 확인은 제외하고 해시된 비밀번호 저장)
    user_dict = user_data.model_dump(exclude={"password", "password_confirm"})
    user_dict.update({
        "hashed_password": hashed_password,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "active": True
    })

    try:
        # Firestore에 사용자 데이터 저장
        user_ref = users_ref.document()  # 자동 ID 생성
        user_ref.set(user_dict)
        
        # 응답 데이터 준비
        user_response = UserResponse(
            id=user_ref.id,
            userid=user_data.userid,
            name=user_data.name,
            email=user_data.email
        )
        
        logger.info(f"사용자 생성 완료: {user_data.email}, ID: {user_ref.id}")
        return user_response
        
    except Exception as e:
        logger.error(f"사용자 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 등록 중 오류가 발생했습니다."
        ) 