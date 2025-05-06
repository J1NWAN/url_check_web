from config.database import get_db
from .profile_model import ProfileUpdate, ProfileResponse
from util.util import get_password_hash, verify_password
from fastapi import HTTPException, status
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_profile(user_id: str, profile_data: ProfileUpdate) -> ProfileResponse:
    """
    사용자 프로필 정보를 업데이트합니다.
    
    Args:
        user_id: 사용자 ID (Firestore 문서 ID)
        profile_data: 업데이트할 프로필 정보
        
    Returns:
        업데이트된 사용자 프로필 정보
        
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
        user_ref = db.collection('user').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            logger.warning(f"프로필 업데이트 실패: 존재하지 않는 사용자 ID - {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자 정보를 찾을 수 없습니다."
            )
        
        # 사용자 데이터 가져오기
        user_data = user_doc.to_dict()
        
        # 업데이트할 데이터 준비
        update_data = {
            "email": profile_data.email,
            "updated_at": datetime.now()
        }
        
        # 선택적 필드 업데이트
        if profile_data.phone is not None:
            update_data["phone"] = profile_data.phone
            
        if profile_data.bio is not None:
            update_data["bio"] = profile_data.bio
            
        # 비밀번호 변경 처리
        if profile_data.new_password:
            # 이전 비밀번호와 동일한지 확인
            if verify_password(profile_data.new_password, user_data.get("password")):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="새 비밀번호는 이전 비밀번호와 동일할 수 없습니다."
                )
            
            # 비밀번호 해싱
            update_data["password"] = get_password_hash(profile_data.new_password)
        
        # Firestore 문서 업데이트
        user_ref.update(update_data)
        
        # 업데이트된 사용자 정보 조회
        updated_user = user_ref.get().to_dict()
        
        return ProfileResponse(
            id=user_id,
            userid=updated_user.get("userid"),
            name=updated_user.get("name"),
            email=updated_user.get("email"),
            phone=updated_user.get("phone"),
            bio=updated_user.get("bio")
        )
        
    except HTTPException:
        # 이미 처리된 HTTPException은 그대로 전파
        raise
    except Exception as e:
        logger.error(f"프로필 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프로필 업데이트 중 오류가 발생했습니다."
        )
