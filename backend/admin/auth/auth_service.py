from util.util import get_password_hash, verify_password, create_access_token
from config.database import get_db
from .auth_model import UserCreate, UserResponse, UserLogin, Token, CurrentUser, AuthItem
from fastapi import HTTPException, status
import logging
from datetime import datetime, timedelta

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
            detail=f"이미 사용 중인 아이디입니다: {user_data.userid}"
        )
    
    # 이메일 중복 확인
    email_query = users_ref.where('email', '==', user_data.email).limit(1).stream()
    if any(email_query):
        logger.warning(f"이미 등록된 이메일로 가입 시도: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"이미 가입된 이메일 주소입니다: {user_data.email}"
        )

    # 비밀번호 해싱
    hashed_password = get_password_hash(user_data.password)
    
    # 사용자 데이터 준비 (비밀번호와 비밀번호 확인은 제외하고 해시된 비밀번호 저장)
    user_dict = user_data.model_dump(exclude={"password", "password_confirm"})
    user_dict.update({
        "password": hashed_password,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
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

async def login_user(login_data: UserLogin) -> Token:
    """
    사용자 로그인 처리 및 액세스 토큰 발급
    
    Args:
        login_data: 로그인 정보 (아이디, 비밀번호)
        
    Returns:
        액세스 토큰 및 사용자 정보가 담긴 응답
        
    Raises:
        HTTPException: 데이터베이스 연결 오류, 로그인 실패(잘못된 아이디/비밀번호) 등
    """
    # 데이터베이스 연결
    db = get_db()
    if db is None:
        logger.error("데이터베이스 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 연결 오류가 발생했습니다."
        )
    
    # 사용자 조회
    users_ref = db.collection('user')
    user_query = users_ref.where('userid', '==', login_data.userid).limit(1).stream()
    
    # 사용자 검증
    user_doc = next((doc for doc in user_query), None)
    
    if not user_doc:
        logger.warning(f"로그인 실패: 존재하지 않는 아이디 - {login_data.userid}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다."
        )
    
    # 사용자 데이터 가져오기
    user_data = user_doc.to_dict()
    
    # 비밀번호 검증
    if not verify_password(login_data.password, user_data.get("password")):
        logger.warning(f"로그인 실패: 잘못된 비밀번호 - {login_data.userid}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다."
        )
    
    # 로그인 성공 처리
    logger.info(f"로그인 성공: {login_data.userid}")
    
    # 사용자 권한 정보 가져오기
    auth_info = None
    
    # DB에 이미 auth 배열이 있는 경우
    if user_data.get("auth") and isinstance(user_data.get("auth"), list) and len(user_data.get("auth")) > 0:
        # 첫 번째 권한 항목만 토큰에 포함 (단순화)
        auth_item = user_data.get("auth")[0]
        if isinstance(auth_item, dict) and "role" in auth_item:
            auth_info = {"role": auth_item["role"]}
    # 기존 role 필드가 있는 경우
    elif user_data.get("role"):
        auth_info = {"role": user_data.get("role")}
    # 둘 다 없는 경우 기본값
    else:
        auth_info = {"role": "user"}
    
    # 토큰에 담을 데이터
    token_data = {
        "sub": user_doc.id,
        "userid": user_data.get("userid"),
        "name": user_data.get("name"),
        "auth": auth_info  # auth 정보 추가
    }
    
    # 토큰 생성
    access_token = create_access_token(token_data)
    
    return Token(
        access_token=access_token,
        user_id=user_doc.id,
        userid=user_data.get("userid"),
        name=user_data.get("name")
    )

async def get_current_user(user_id: str) -> CurrentUser:
    """
    사용자 ID로 현재 로그인된 사용자 정보를 조회합니다.
    
    Args:
        user_id: 사용자 ID (Firestore 문서 ID)
        
    Returns:
        현재 사용자 정보
        
    Raises:
        HTTPException: 데이터베이스 연결 오류 또는 사용자를 찾을 수 없는 경우
    """
    # 데이터베이스 연결
    db = get_db()
    if db is None:
        logger.error("데이터베이스 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 연결 오류가 발생했습니다."
        )
    
    try:
        # 사용자 문서 조회
        user_doc = db.collection('user').document(user_id).get()
        
        if not user_doc.exists:
            logger.warning(f"사용자 정보 조회 실패: 존재하지 않는 사용자 ID - {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자 정보를 찾을 수 없습니다."
            )
        
        # 사용자 데이터 가져오기
        user_data = user_doc.to_dict()
        
        # 응답 데이터 준비
        created_at = user_data.get("created_at")
        if created_at and isinstance(created_at, datetime):
            created_at_str = created_at.isoformat()
        else:
            created_at_str = None
            
        # 사용자 auth 정보 처리
        auth_items = []
        
        # DB에 이미 auth 배열이 있는 경우 그대로 사용
        if user_data.get("auth"):
            auth_items = user_data.get("auth")
        # 기존 role 필드가 있는 경우 auth 배열로 변환
        elif user_data.get("role"):
            role = user_data.get("role")
            
            # role에 따른 역할명 지정
            role_name = "일반 사용자"
            if role == "admin":
                role_name = "관리자"
            elif role == "super-admin":
                role_name = "슈퍼 관리자"
                
            # AuthItem 객체 생성
            auth_items = [AuthItem(role=role, role_name=role_name)]
        # 둘 다 없는 경우 기본값으로 일반 사용자 권한 설정
        else:
            auth_items = [AuthItem(role="user", role_name="일반 사용자")]
        
        return CurrentUser(
            id=user_doc.id,
            userid=user_data.get("userid"),
            name=user_data.get("name"),
            email=user_data.get("email"),
            auth=auth_items,
            created_at=created_at_str,
            phone=user_data.get("phone"),
            bio=user_data.get("bio"),
            profile_color=user_data.get("profile_color")
        )
        
    except HTTPException:
        # 이미 처리된 HTTPException은 그대로 전파
        raise
    except Exception as e:
        logger.error(f"사용자 정보 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 조회 중 오류가 발생했습니다."
        ) 