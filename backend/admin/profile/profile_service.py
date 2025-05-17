from config.database import get_db
from .profile_model import ProfileUpdate, ProfileResponse, AdminUserResponse, AdminListResponse, AdminUpdateRequest, AuthItem
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
    자신을 제외한 모든 사용자 목록을 가져옵니다.
    
    Args:
        current_user_id: 현재 로그인한 사용자 ID
        
    Returns:
        사용자 목록이 담긴 응답
        
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
        # 사용자 컬렉션에서 모든 사용자 조회
        users_ref = db.collection('user')
        users_query = users_ref.stream()
        
        # 사용자 목록 생성
        admin_list = []
        for doc in users_query:
            # 자기 자신은 제외
            if doc.id == current_user_id:
                continue
                
            user_data = doc.to_dict()
            
            # 권한 정보 처리
            auth_items = []
            
            # DB에 이미 auth 배열이 있는 경우
            if user_data.get("auth") and isinstance(user_data.get("auth"), list):
                auth_items = [AuthItem(**item) if isinstance(item, dict) else item for item in user_data.get("auth")]
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
            
            admin_list.append(
                AdminUserResponse(
                    id=doc.id,
                    userid=user_data.get("userid"),
                    name=user_data.get("name"),
                    email=user_data.get("email"),
                    phone=user_data.get("phone"),
                    bio=user_data.get("bio"),
                    profile_color=user_data.get("profile_color", "#000000"),
                    auth=auth_items
                )
            )
        
        return AdminListResponse(admins=admin_list)
        
    except Exception as e:
        logger.error(f"사용자 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 목록 조회 중 오류가 발생했습니다."
        )

async def get_admin_detail(admin_id: str) -> AdminUserResponse:
    """
    관리자 상세 정보를 조회합니다.
    
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
            logger.warning(f"사용자 정보 조회 실패: 존재하지 않는 사용자 ID - {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자 정보를 찾을 수 없습니다."
            )
        
        # 사용자 데이터 가져오기
        user_data = user_doc.to_dict()
        
        # 권한 정보 처리
        auth_items = []
        
        # DB에 이미 auth 배열이 있는 경우
        if user_data.get("auth") and isinstance(user_data.get("auth"), list):
            auth_items = [AuthItem(**item) if isinstance(item, dict) else item for item in user_data.get("auth")]
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
        
        return AdminUserResponse(
            id=admin_id,
            userid=user_data.get("userid"),
            name=user_data.get("name"),
            email=user_data.get("email"),
            phone=user_data.get("phone"),
            bio=user_data.get("bio"),
            profile_color=user_data.get("profile_color", "#000000"),
            auth=auth_items
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

async def update_admin(admin_id: str, admin_data: AdminUpdateRequest, current_user_id: str) -> AdminUserResponse:
    """
    관리자 정보를 업데이트합니다.
    
    Args:
        admin_id: 업데이트할 관리자 ID
        admin_data: 업데이트할 관리자 정보
        current_user_id: 현재 로그인한 사용자 ID
        
    Returns:
        업데이트된 관리자 정보
        
    Raises:
        HTTPException: 데이터베이스 연결 오류, 권한 부족, 또는 사용자를 찾을 수 없는 경우
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
            logger.warning(f"관리자 정보 업데이트 실패: 존재하지 않는 사용자 ID - {admin_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자 정보를 찾을 수 없습니다."
            )
        
        # 사용자 데이터 가져오기
        user_data = user_doc.to_dict()
        logger.info(f"업데이트할 관리자 정보: {user_data}")
        
        # 업데이트할 데이터 준비
        update_data = {
            "email": admin_data.email,
            "updated_at": datetime.now()
        }
        
        # 선택적 필드 업데이트
        if admin_data.phone is not None:
            update_data["phone"] = admin_data.phone
            
        if admin_data.bio is not None:
            update_data["bio"] = admin_data.bio
            
        if admin_data.profile_color is not None:
            update_data["profile_color"] = admin_data.profile_color
        
        # 권한 업데이트 (이미 라우터에서 super-admin 권한 검증 완료)
        if admin_data.auth is not None:
            logger.info(f"권한 업데이트: {admin_data.auth}")
            
            # auth 배열 데이터 준비
            auth_list = []
            for auth_item in admin_data.auth:
                auth_list.append({
                    "role": auth_item.role,
                    "role_name": auth_item.role_name
                })
            
            # Firestore에 저장 (빈 배열인 경우도 저장)
            update_data["auth"] = auth_list
            
            # 기존 role 필드 제거 (호환성을 위해 유지할 수도 있음)
            # 첫 번째 권한 정보가 있으면 role 필드에도 저장
            if auth_list and auth_list[0]["role"]:
                update_data["role"] = auth_list[0]["role"]
            else:
                update_data["role"] = None
            
        # 비밀번호 변경 처리
        if admin_data.new_password:
            # 비밀번호 해싱
            update_data["password"] = get_password_hash(admin_data.new_password)
        
        # Firestore 문서 업데이트
        logger.info(f"업데이트할 데이터: {update_data}")
        user_ref.update(update_data)
        
        # 업데이트된 사용자 정보 조회
        updated_user = user_ref.get().to_dict()
        
        # auth 정보 처리
        auth_items = []
        
        # DB에 이미 auth 배열이 있는 경우
        if updated_user.get("auth") and isinstance(updated_user.get("auth"), list):
            auth_items = [AuthItem(**item) if isinstance(item, dict) else item for item in updated_user.get("auth")]
        # 기존 role 필드가 있는 경우 auth 배열로 변환
        elif updated_user.get("role"):
            role = updated_user.get("role")
            
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
        
        return AdminUserResponse(
            id=admin_id,
            userid=updated_user.get("userid"),
            name=updated_user.get("name"),
            email=updated_user.get("email"),
            phone=updated_user.get("phone"),
            bio=updated_user.get("bio"),
            profile_color=updated_user.get("profile_color"),
            auth=auth_items
        )
        
    except HTTPException:
        # 이미 처리된 HTTPException은 그대로 전파
        raise
    except Exception as e:
        logger.error(f"관리자 정보 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 정보 업데이트 중 오류가 발생했습니다."
        )

async def get_user_auth(user_id: str) -> str:
    """
    사용자의 권한 정보를 조회합니다.
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        사용자 권한 (user, admin, super-admin)
        
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
            logger.warning(f"사용자 권한 조회 실패: 존재하지 않는 사용자 ID - {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자 정보를 찾을 수 없습니다."
            )
        
        # 사용자 데이터 가져오기
        user_data = user_doc.to_dict()
        
        # auth 정보 먼저 확인
        if user_data.get("auth") and isinstance(user_data.get("auth"), list) and len(user_data.get("auth")) > 0:
            auth_item = user_data.get("auth")[0]
            if isinstance(auth_item, dict) and "role" in auth_item:
                role = auth_item["role"]
                logger.info(f"사용자 {user_id}의 권한(auth): {role}")
                return role
        
        # auth 정보가 없으면 기존 role 필드 확인
        role = user_data.get("role", "user")
        logger.info(f"사용자 {user_id}의 권한(role): {role}")
        
        return role
        
    except HTTPException:
        # 이미 처리된 HTTPException은 그대로 전파
        raise
    except Exception as e:
        logger.error(f"사용자 권한 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 권한 조회 중 오류가 발생했습니다."
        )
