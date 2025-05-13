from config.database import get_db
from .profile_model import ProfileUpdate, ProfileResponse, AdminUserResponse, AdminListResponse
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
            
        if profile_data.profile_color is not None:
            update_data["profile_color"] = profile_data.profile_color
            
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
            bio=updated_user.get("bio"),
            profile_color=updated_user.get("profile_color")
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

async def get_admin_list(current_user_id: str) -> AdminListResponse:
    """
    자신을 제외한 모든 관리자 목록을 가져옵니다.
    
    Args:
        current_user_id: 현재 로그인한 사용자 ID
        
    Returns:
        관리자 목록이 담긴 응답
        
    Raises:
        HTTPException: 데이터베이스 연결 오류 또는 조회 중 오류 발생 시
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
        # 사용자 컬렉션에서 관리자 권한을 가진 사용자 조회
        # role이 'admin' 또는 'super-admin'인 사용자를 모두 가져옴
        users_ref = db.collection('user')
        admin_query = users_ref.where('role', 'in', ['admin', 'super-admin']).stream()
        
        # 관리자 목록 생성
        admin_list = []
        for doc in admin_query:
            # 자기 자신은 제외
            if doc.id == current_user_id:
                continue
                
            user_data = doc.to_dict()
            admin_list.append(
                AdminUserResponse(
                    id=doc.id,
                    userid=user_data.get("userid"),
                    name=user_data.get("name"),
                    email=user_data.get("email"),
                    phone=user_data.get("phone"),
                    bio=user_data.get("bio"),
                    profile_color=user_data.get("profile_color", "#000000"),
                    role=user_data.get("role", "user")
                )
            )
        
        return AdminListResponse(admins=admin_list)
        
    except Exception as e:
        logger.error(f"관리자 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 목록 조회 중 오류가 발생했습니다."
        )

async def get_admin_detail(admin_id: str) -> AdminUserResponse:
    """
    특정 관리자의 상세 정보를 가져옵니다.
    
    Args:
        admin_id: 조회할 관리자 ID
        
    Returns:
        관리자 상세 정보
        
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
        user_ref = db.collection('user').document(admin_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            logger.warning(f"관리자 정보 조회 실패: 존재하지 않는 사용자 ID - {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 정보를 찾을 수 없습니다."
            )
        
        # 사용자 데이터 가져오기
        user_data = user_doc.to_dict()
        
        # 관리자 권한 확인 (선택 사항)
        role = user_data.get("role", "user")
        if role not in ["admin", "super-admin"]:
            logger.warning(f"관리자 권한이 없는 사용자 조회 시도: {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="관리자 권한이 없는 사용자입니다."
            )
        
        return AdminUserResponse(
            id=admin_id,
            userid=user_data.get("userid"),
            name=user_data.get("name"),
            email=user_data.get("email"),
            phone=user_data.get("phone"),
            bio=user_data.get("bio"),
            profile_color=user_data.get("profile_color", "#000000"),
            role=role
        )
        
    except HTTPException:
        # 이미 처리된 HTTPException은 그대로 전파
        raise
    except Exception as e:
        logger.error(f"관리자 정보 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 정보 조회 중 오류가 발생했습니다."
        )
