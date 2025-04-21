from config.database import get_db
from .system_model import SystemCreate, SystemResponse, SystemUpdate
from fastapi import HTTPException, status
import logging
from datetime import datetime
from typing import List, Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLLECTION = "systems"

# datetime 객체를 Firestore에 저장 가능한 형식으로 변환
def _prepare_dict_for_firestore(data: dict) -> dict:
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            # Firestore에서는 datetime 객체를 직접 저장할 수 있지만, 
            # 확실하게 하기 위해 ISO 형식 문자열로 변환
            result[key] = value.isoformat()
        elif isinstance(value, list) and key == "menus":
            # menus 리스트의 각 아이템을 dict로 변환 (Pydantic 모델은 직렬화 필요)
            result[key] = [item.dict() if hasattr(item, 'dict') else item for item in value]
        else:
            result[key] = value
    return result

async def create_system(system_data: SystemCreate) -> SystemResponse:
    """시스템 생성 서비스"""
    db = get_db()
    if db is None:
        logger.error("데이터베이스 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 연결 오류가 발생했습니다."
        )
    
    try:
        # 시스템 데이터를 딕셔너리로 변환하고 Firestore에 맞게 가공
        system_dict = system_data.dict()
        system_dict = _prepare_dict_for_firestore(system_dict)
        
        # Firestore에 저장 (await 제거)
        new_system_ref = db.collection(COLLECTION).document()
        new_system_ref.set(system_dict)
        
        # 응답 데이터 구성
        response_data = {**system_dict, "id": new_system_ref.id}
        
        # ISO 문자열로 변환된 날짜를 다시 datetime 객체로 변환
        if isinstance(response_data.get('created_at'), str):
            response_data['created_at'] = datetime.fromisoformat(response_data['created_at'])
        
        return SystemResponse(**response_data)
    except Exception as e:
        logger.error(f"시스템 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 생성 중 오류가 발생했습니다: {str(e)}"
        )

async def get_systems() -> List[SystemResponse]:
    """모든 시스템 목록 조회 서비스"""
    db = get_db()
    if db is None:
        logger.error("데이터베이스 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 연결 오류가 발생했습니다."
        )
    
    try:
        # Firestore에서 모든 시스템 데이터 조회
        systems_ref = db.collection(COLLECTION)
        systems = []
        
        for doc in systems_ref.stream():
            system_data = doc.to_dict()
            system_data["id"] = doc.id
            
            # ISO 문자열로 변환된 날짜를 다시 datetime 객체로 변환
            for date_field in ['created_at', 'updated_at']:
                if isinstance(system_data.get(date_field), str):
                    system_data[date_field] = datetime.fromisoformat(system_data[date_field])
            
            systems.append(SystemResponse(**system_data))
        
        return systems
    except Exception as e:
        logger.error(f"시스템 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

async def get_system(system_id: str) -> Optional[SystemResponse]:
    """특정 시스템 조회 서비스"""
    db = get_db()
    if db is None:
        logger.error("데이터베이스 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 연결 오류가 발생했습니다."
        )
    
    try:
        # Firestore에서 특정 시스템 데이터 조회
        system_ref = db.collection(COLLECTION).document(system_id)
        system_doc = system_ref.get()
        
        if not system_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {system_id}인 시스템을 찾을 수 없습니다."
            )
        
        system_data = system_doc.to_dict()
        system_data["id"] = system_id
        
        # ISO 문자열로 변환된 날짜를 다시 datetime 객체로 변환
        for date_field in ['created_at', 'updated_at']:
            if isinstance(system_data.get(date_field), str):
                system_data[date_field] = datetime.fromisoformat(system_data[date_field])
        
        return SystemResponse(**system_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 조회 중 오류가 발생했습니다: {str(e)}"
        )

async def update_system(system_id: str, system_data: SystemUpdate) -> SystemResponse:
    """시스템 정보 업데이트 서비스"""
    db = get_db()
    if db is None:
        logger.error("데이터베이스 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 연결 오류가 발생했습니다."
        )
    
    try:
        # 기존 시스템 데이터 확인
        system_ref = db.collection(COLLECTION).document(system_id)
        system_doc = system_ref.get()
        
        if not system_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {system_id}인 시스템을 찾을 수 없습니다."
            )
        
        # 수정할 필드만 추출하여 업데이트
        update_data = {k: v for k, v in system_data.dict().items() if v is not None}
        update_data = _prepare_dict_for_firestore(update_data)
        system_ref.update(update_data)
        
        # 업데이트된 데이터 반환
        updated_system = system_ref.get().to_dict()
        updated_system["id"] = system_id
        
        # ISO 문자열로 변환된 날짜를 다시 datetime 객체로 변환
        for date_field in ['created_at', 'updated_at']:
            if isinstance(updated_system.get(date_field), str):
                updated_system[date_field] = datetime.fromisoformat(updated_system[date_field])
        
        return SystemResponse(**updated_system)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 업데이트 중 오류가 발생했습니다: {str(e)}"
        )

async def delete_system(system_id: str) -> bool:
    """시스템 삭제 서비스"""
    db = get_db()
    if db is None:
        logger.error("데이터베이스 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 연결 오류가 발생했습니다."
        )
    
    try:
        # 기존 시스템 데이터 확인
        system_ref = db.collection(COLLECTION).document(system_id)
        system_doc = system_ref.get()
        
        if not system_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {system_id}인 시스템을 찾을 수 없습니다."
            )
        
        # 시스템 삭제
        system_ref.delete()
        
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 삭제 중 오류가 발생했습니다: {str(e)}"
        )