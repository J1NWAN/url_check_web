import logging
from datetime import datetime
from typing import List, Optional, Dict
from google.cloud.firestore import CollectionReference
from config.database import get_db
from .history_model import (
    InspectionHistory, 
    InspectionResult,
    SystemInspectionSummary,
    LatestInspectionResult,
    SystemStatistics,
    InspectionHistorySummary
)

# 로거 설정
logger = logging.getLogger(__name__)

# 컬렉션 이름
INSPECTION_HISTORY_COLLECTION = "inspection_history"
SYSTEMS_COLLECTION = "systems"

def get_inspection_history_collection() -> CollectionReference:
    """점검 이력 컬렉션 참조를 반환합니다."""
    db = get_db()
    return db.collection(INSPECTION_HISTORY_COLLECTION)

def get_systems_collection() -> CollectionReference:
    """시스템 컬렉션 참조를 반환합니다."""
    db = get_db()
    return db.collection(SYSTEMS_COLLECTION)

async def get_system_list() -> List[Dict]:
    """시스템 목록을 가져옵니다."""
    systems = []
    try:
        systems_ref = get_systems_collection()
        docs = systems_ref.stream()
        
        for doc in docs:
            system_data = doc.to_dict()
            system_data["id"] = doc.id
            systems.append(system_data)
        
        return systems
    except Exception as e:
        logger.error(f"시스템 목록 조회 오류: {str(e)}")
        return []

async def get_latest_inspection_result(system_id: str) -> Optional[LatestInspectionResult]:
    """시스템의 최신 점검 결과를 가져옵니다."""
    try:
        history_ref = get_inspection_history_collection()
        
        # 모든 점검 이력 문서 가져오기 (최신순)
        docs = list(history_ref.order_by("created_at", direction="DESCENDING").limit(30).stream())
        
        if not docs:
            return None
        
        # 최신 점검 결과 찾기
        for doc in docs:
            doc_data = doc.to_dict()
            if "inspection_systems" not in doc_data:
                continue
                
            # inspection_systems 배열에서 해당 시스템 ID와 일치하는 항목 찾기
            for system_inspection in doc_data["inspection_systems"]:
                if system_inspection.get("system_id") == system_id:
                    # 최신 점검 결과 찾음
                    inspection_date = system_inspection.get("inspection_end") or system_inspection.get("inspection_start")
                    
                    # 점검 결과에서 오류 여부 확인
                    has_error = False
                    for result in system_inspection.get("inspection_results", []):
                        status_code = result.get("status_code", 0)
                        if status_code < 200 or status_code >= 400:
                            has_error = True
                            break
                    
                    return LatestInspectionResult(
                        inspection_date=inspection_date,
                        has_error=has_error
                    )
        
        # 결과가 없는 경우
        return None
    
    except Exception as e:
        logger.error(f"최신 점검 결과 조회 오류 (system_id: {system_id}): {str(e)}")
        return None

async def get_system_statistics(system_id: str) -> SystemStatistics:
    """시스템의 점검 통계를 계산합니다."""
    statistics = SystemStatistics()
    
    try:
        history_ref = get_inspection_history_collection()
        # 모든 점검 이력 문서 가져오기
        docs = list(history_ref.stream())
        
        total_count = 0
        error_count = 0
        
        # 각 문서 확인
        for doc in docs:
            doc_data = doc.to_dict()
            if "inspection_systems" not in doc_data:
                continue
                
            # inspection_systems 배열에서 해당 시스템 ID와 일치하는 항목 찾기
            for system_inspection in doc_data["inspection_systems"]:
                if system_inspection.get("system_id") == system_id:
                    total_count += 1
                    
                    # 점검 결과에서 오류 여부 확인
                    has_error_in_results = False
                    for result in system_inspection.get("inspection_results", []):
                        status_code = result.get("status_code", 0)
                        if status_code < 200 or status_code >= 400:
                            has_error_in_results = True
                            break
                    
                    if has_error_in_results:
                        error_count += 1
        
        statistics.total_inspections = total_count
        statistics.error_count = error_count
        statistics.success_count = total_count - error_count
        
        # 성공률 계산 (점검 이력이 없는 경우 0으로 설정)
        if total_count > 0:
            statistics.success_rate = round((statistics.success_count / total_count) * 100, 1)
        
        return statistics
    
    except Exception as e:
        logger.error(f"시스템 통계 계산 오류 (system_id: {system_id}): {str(e)}")
        return statistics

async def get_inspection_history_summary() -> InspectionHistorySummary:
    """모든 시스템의 점검 이력 요약 정보를 가져옵니다."""
    summary = InspectionHistorySummary()
    
    try:
        # 시스템 목록 가져오기
        systems = await get_system_list()
        
        for system in systems:
            system_id = system.get("id")
            system_name = system.get("kor_name", "알 수 없는 시스템")
            
            # 최신 점검 결과 가져오기
            latest_result = await get_latest_inspection_result(system_id)
            
            # 통계 정보 가져오기
            statistics = await get_system_statistics(system_id)
            
            # 시스템 요약 정보 생성
            system_summary = SystemInspectionSummary(
                system_id=system_id,
                system_name=system_name,
                latest_result=latest_result,
                statistics=statistics
            )
            
            # 전체 요약에 추가
            summary.systems.append(system_summary)
        
        return summary
    
    except Exception as e:
        logger.error(f"점검 이력 요약 정보 조회 오류: {str(e)}")
        return summary

async def get_system_inspection_history(system_id: str) -> List[InspectionHistory]:
    """특정 시스템의 점검 이력을 가져옵니다."""
    history_list = []
    
    try:
        # 시스템 정보 확인
        system_info = None
        systems_ref = get_systems_collection()
        system_doc = systems_ref.document(system_id).get()
        
        if system_doc.exists:
            system_info = system_doc.to_dict()
        
        if not system_info:
            logger.warning(f"시스템을 찾을 수 없습니다 (system_id: {system_id})")
            return []
        
        # 시스템 이름
        system_name = system_info.get("kor_name", "알 수 없는 시스템")
        
        # 점검 이력 가져오기
        history_ref = get_inspection_history_collection()
        # 모든 점검 이력 문서 가져오기 (최신순)
        docs = list(history_ref.order_by("created_at", direction="DESCENDING").stream())
        
        # 해당 시스템의 점검 이력 추출
        for doc in docs:
            doc_data = doc.to_dict()
            doc_id = doc.id
            
            if "inspection_systems" not in doc_data:
                continue
            
            # 문서 내의 inspection_systems 배열에서 해당 시스템 ID와 일치하는 항목 찾기
            for system_inspection in doc_data["inspection_systems"]:
                if system_inspection.get("system_id") == system_id:
                    # 점검 일시
                    inspection_date = system_inspection.get("inspection_end") or system_inspection.get("inspection_start")
                    
                    # 메뉴 점검 결과 변환
                    results = []
                    has_error = False
                    
                    for result_data in system_inspection.get("inspection_results", []):
                        status_code = result_data.get("status_code", 0)
                        is_error = status_code < 200 or status_code >= 400
                        
                        if is_error:
                            has_error = True
                        
                        result = InspectionResult(
                            url=result_data.get("path", ""),
                            status_code=status_code,
                            response_time=result_data.get("response_time"),
                            error_message=result_data.get("error_message"),
                            is_error=is_error,
                            inspection_date=inspection_date
                        )
                        results.append(result)
                    
                    # 점검 이력 객체 생성
                    history_id = system_inspection.get("id") or f"{system_id}_{doc_id}"
                    history = InspectionHistory(
                        id=history_id,
                        system_id=system_id,
                        system_name=system_name,
                        inspection_date=inspection_date,
                        results=results,
                        has_error=has_error,
                        summary={
                            "inspection_type": system_inspection.get("inspection_type", "자동"),
                            "created_by": system_inspection.get("created_by", "system")
                        }
                    )
                    
                    history_list.append(history)
                    break  # 이 문서에서 해당 시스템을 찾았으므로 다음 문서로 이동
        
        return history_list
    
    except Exception as e:
        logger.error(f"시스템 점검 이력 조회 오류 (system_id: {system_id}): {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []
