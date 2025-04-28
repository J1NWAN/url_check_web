from config.database import get_db
from .system_model import SystemCreate, SystemResponse, SystemUpdate, SystemInspectionCreate, SystemInspectionUpdate, SystemInspectionResponse, InspectionMenuResult
from fastapi import HTTPException, status
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import aiohttp
import asyncio
import time
from google.cloud import firestore

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLLECTION = "systems"

# 점검 이력 컬렉션 이름
INSPECTION_COLLECTION = "system_inspections"

# HTTP 상태 코드에 대한 한글 설명
HTTP_STATUS_TEXT = {
    200: "정상",
    201: "생성됨",
    301: "영구 이동",
    302: "임시 이동",
    400: "잘못된 요청",
    401: "인증 실패",
    403: "접근 금지",
    404: "찾을 수 없음",
    500: "서버 내부 오류",
    502: "게이트웨이 오류",
    503: "서비스 사용 불가",
    504: "게이트웨이 시간 초과"
}

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

async def perform_system_inspection(system_id: str, inspection_type: str, created_by: str, inspection_results=None) -> Dict[str, Any]:
    """시스템 URL 연결 상태 점검 수행 함수 (저장하지 않고 결과만 반환)"""
    db = get_db()
    if db is None:
        logger.error("데이터베이스 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 연결 오류가 발생했습니다."
        )
    
    try:
        # 시스템 정보 조회
        system_ref = db.collection(COLLECTION).document(system_id)
        system_doc = system_ref.get()
        
        if not system_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {system_id}인 시스템을 찾을 수 없습니다."
            )
        
        system_data = system_doc.to_dict()
        system_url = system_data.get("url")
        system_menus = system_data.get("menus", [])
        
        # 점검 시작 시간 기록
        inspection_start = datetime.now()
        
        # 점검 이력 데이터 생성
        inspection_data = {
            "system_id": system_id,
            "system_eng_name": system_data.get("eng_name", ""),
            "system_kor_name": system_data.get("kor_name", ""),
            "system_url": system_url,
            "inspection_start": inspection_start.isoformat(),
            "inspection_type": inspection_type,
            "created_by": created_by,
            "inspection_results": []
        }
        
        # 초기화
        inspection_results_data = []
        
        # 수동 점검이고 inspection_results가 제공된 경우, 자동 점검을 수행하지 않고 전달받은 결과 사용
        if inspection_type == "수동" and inspection_results:
            logger.info(f"수동 점검 결과 사용: {len(inspection_results)}개 메뉴")
            inspection_results_data = inspection_results
        else:
            # 자동 점검: 각 메뉴별 URL 점검 수행
            async with aiohttp.ClientSession() as session:
                for menu in system_menus:
                    menu_name = menu.get("name", "")
                    menu_path = menu.get("path", "")
                    full_url = f"{system_url}{menu_path}"
                    
                    try:
                        start_time = time.time()
                        async with session.get(full_url, timeout=10) as response:
                            end_time = time.time()
                            response_time = round((end_time - start_time) * 1000, 2)  # ms 단위로 변환
                            
                            # 응답 헤더 가져오기
                            headers = dict(response.headers)
                            # 헤더값을 문자열로 변환
                            headers = {k: str(v) for k, v in headers.items()}
                            
                            # 상태 코드에 대한 한글 설명 추가
                            status_code = response.status
                            status_text = HTTP_STATUS_TEXT.get(status_code, f"알 수 없는 상태 ({status_code})")
                            
                            menu_result = {
                                "menu_name": menu_name,
                                "path": menu_path,
                                "status_code": status_code,
                                "status_text": status_text,
                                "response_time": response_time,
                                "headers": headers
                            }
                            
                            inspection_results_data.append(menu_result)
                    
                    except asyncio.TimeoutError:
                        menu_result = {
                            "menu_name": menu_name,
                            "path": menu_path,
                            "status_code": 408,
                            "status_text": "요청 시간 초과",
                            "response_time": 10000,  # 10초 타임아웃
                            "headers": {}
                        }
                        inspection_results_data.append(menu_result)
                    
                    except Exception as e:
                        menu_result = {
                            "menu_name": menu_name,
                            "path": menu_path,
                            "status_code": 0,
                            "status_text": f"오류 발생: {str(e)}",
                            "response_time": 0,
                            "headers": {}
                        }
                        inspection_results_data.append(menu_result)
        
        # 점검 종료 시간 기록
        inspection_end = datetime.now()
        
        # 점검 결과 업데이트
        inspection_data["inspection_end"] = inspection_end.isoformat()
        inspection_data["inspection_results"] = inspection_results_data
        
        # 고유 ID 생성
        unique_id = f"{system_id}_{int(inspection_start.timestamp())}"
        inspection_data["id"] = unique_id
        
        # ISO 문자열로 변환된 날짜를 datetime 객체로 변환하여 응답용 데이터 생성
        response_data = dict(inspection_data)
        response_data["inspection_start"] = inspection_start
        response_data["inspection_end"] = inspection_end
        
        return inspection_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 점검 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 점검 중 오류가 발생했습니다: {str(e)}"
        )

async def save_inspection_history(inspection_systems: List[Dict[str, Any]], document_id: str = None) -> str:
    """점검 이력을 저장하는 함수"""
    db = get_db()
    if db is None:
        logger.error("데이터베이스 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 연결 오류가 발생했습니다."
        )
    
    try:
        # 문서 ID가 제공되지 않은 경우 현재 시간으로 생성
        if not document_id:
            document_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        inspections_ref = db.collection(INSPECTION_COLLECTION).document(document_id)
        
        # 문서 생성
        inspections_ref.set({
            "inspection_systems": inspection_systems,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        return document_id
    
    except Exception as e:
        logger.error(f"점검 이력 저장 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"점검 이력 저장 중 오류가 발생했습니다: {str(e)}"
        )

async def inspect_system(system_id: str, inspection_type: str, created_by: str, inspection_results=None) -> SystemInspectionResponse:
    """시스템 URL 연결 상태 점검 서비스 (점검 실행 및 결과 저장)"""
    try:
        # 점검 실행
        inspection_data = await perform_system_inspection(system_id, inspection_type, created_by, inspection_results)
        
        # 이력 저장 (개별 시스템 점검의 경우 문서 ID 자동 생성)
        await save_inspection_history([inspection_data])
        
        # ISO 문자열로 변환된 날짜를 datetime 객체로 변환
        for date_field in ['inspection_start', 'inspection_end']:
            if isinstance(inspection_data.get(date_field), str):
                inspection_data[date_field] = datetime.fromisoformat(inspection_data[date_field])
        
        return SystemInspectionResponse(**inspection_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 점검 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 점검 중 오류가 발생했습니다: {str(e)}"
        )

async def get_system_inspections(system_id: str, limit: int = 10) -> List[SystemInspectionResponse]:
    """시스템의 점검 이력 조회 서비스"""
    db = get_db()
    if db is None:
        logger.error("데이터베이스 연결 실패")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 연결 오류가 발생했습니다."
        )
    
    try:
        # 시스템 정보 확인
        system_ref = db.collection(COLLECTION).document(system_id)
        system_doc = system_ref.get()
        
        if not system_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {system_id}인 시스템을 찾을 수 없습니다."
            )
        
        # 전체 점검 이력 문서 조회 (최신 문서부터 - 문서 이름이 타임스탬프 형식이므로 이름 기준 내림차순)
        inspections_query = (
            db.collection(INSPECTION_COLLECTION)
            .order_by("__name__", direction="DESCENDING")
            .limit(50)  # 최근 50개 문서만 조회
        )
        
        inspections = []
        # 모든 문서를 조회하여 해당 시스템의 점검 이력 필터링
        for doc in inspections_query.stream():
            doc_data = doc.to_dict()
            if "inspection_systems" in doc_data:
                for inspection in doc_data["inspection_systems"]:
                    if inspection.get("system_id") == system_id:
                        # ISO 문자열로 변환된 날짜를 다시 datetime 객체로 변환
                        for date_field in ['inspection_start', 'inspection_end']:
                            if isinstance(inspection.get(date_field), str):
                                inspection[date_field] = datetime.fromisoformat(inspection[date_field])
                        
                        # 응답용 ID 생성
                        if "id" not in inspection:
                            inspection["id"] = f"{system_id}_{int(inspection['inspection_start'].timestamp())}"
                        
                        inspections.append(SystemInspectionResponse(**inspection))
            
            # 필요한 개수의 이력을 찾았으면 중단
            if len(inspections) >= limit:
                break
        
        # limit 적용 (정렬 후)
        inspections.sort(key=lambda x: x.inspection_start, reverse=True)
        return inspections[:limit]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 점검 이력 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 점검 이력 조회 중 오류가 발생했습니다: {str(e)}"
        )