import logging
from datetime import datetime, timedelta
from config.database import get_db
from fastapi import HTTPException, status
import json

# 로거 설정
logger = logging.getLogger(__name__)

async def get_dashboard_statistics():
    """대시보드에 표시할 통계 정보를 조회하는 서비스 함수"""
    try:
        db = get_db()
        if not db:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="데이터베이스 연결 오류"
            )
        
        # 로그 추가: Firestore 컬렉션 확인
        logger.info("대시보드 통계 조회 시작 - Firestore 연결 확인됨")
        
        # 점검 이력 컬렉션 참조
        inspections_ref = db.collection('inspection_history')
        
        # 모든 문서 가져와서 직접 필터링하기
        all_inspections = list(inspections_ref.get())
        logger.info(f"전체 inspection_history 문서 수: {len(all_inspections)}")
        
        # 첫 번째 문서 구조 확인 (문서가 있는 경우)
        if all_inspections:
            sample_doc = all_inspections[0].to_dict()
            # 민감 정보를 제외하고 로깅
            safe_keys = [k for k in sample_doc.keys()]
            logger.info(f"문서 구조 - 키: {safe_keys}")
            
            # created_at 필드 확인
            created_at = sample_doc.get('created_at') or sample_doc.get('inspection_start')
            if created_at:
                logger.info(f"날짜 필드 타입: {type(created_at)}, 값: {created_at}")
                
                # timestamp 객체 확인
                if hasattr(created_at, 'timestamp'):
                    dt = created_at.timestamp()
                    dt_str = datetime.fromtimestamp(dt).strftime('%Y-%m-%d %H:%M:%S')
                    logger.info(f"변환된 날짜 문자열: {dt_str}")
        
        # 오늘 날짜 계산 (로컬 시간 기준)
        today_local = datetime.now()
        today_str = today_local.strftime('%Y-%m-%d')
        logger.info(f"오늘 날짜 문자열: {today_str}")
        
        # 이번 달 문자열
        this_month_str = today_local.strftime('%Y-%m')
        logger.info(f"이번 달 문자열: {this_month_str}")
        
        # 오늘 점검 내역 수집
        today_inspections = []
        
        for inspection in all_inspections:
            inspection_data = inspection.to_dict()
            # created_at 또는 inspection_start 필드 사용 (하위 호환성)
            date_field = inspection_data.get('created_at') or inspection_data.get('inspection_start')
            
            # 날짜 필드가 없는 경우 스킵
            if not date_field:
                continue
                
            # 디버그 출력 추가: 첫 5개 문서만
            if len(today_inspections) < 5:
                logger.info(f"검사 중인 문서 날짜 필드 타입: {type(date_field)}, 값: {date_field}")
            
            # 날짜 형식에 따라 처리
            is_today = False
            
            # 1. 문자열인 경우
            if isinstance(date_field, str):
                is_today = date_field.startswith(today_str)
            
            # 2. datetime 객체인 경우
            elif isinstance(date_field, datetime):
                is_today = date_field.strftime('%Y-%m-%d') == today_str
            
            # 3. timestamp 객체인 경우 (Firestore 타임스탬프)
            elif hasattr(date_field, 'timestamp'):
                # Firestore Timestamp를 datetime으로 변환
                dt = date_field.timestamp()
                is_today = datetime.fromtimestamp(dt).strftime('%Y-%m-%d') == today_str
            
            if is_today:
                today_inspections.append(inspection)
        
        today_count = len(today_inspections)
        logger.info(f"금일 점검 횟수: {today_count}")
        
        # 시스템 상태 카운트 초기화
        today_success_count = 0
        today_error_count = 0
        
        # 새로운 방식: 각 시스템을 한 번만 집계하기 위한 집합
        system_status = {}  # 시스템 ID => 상태(True: 정상, False: 오류)
        
        # 2, 3. 금일 정상 시스템 및 오류 시스템 수 계산
        for inspection in today_inspections:
            inspection_data = inspection.to_dict()
            
            # inspection_systems 배열이 있는 경우 처리
            if 'inspection_systems' in inspection_data:
                for system in inspection_data['inspection_systems']:
                    system_id = system.get('system_id')
                    if not system_id:
                        continue
                        
                    # 이미 오류로 표시된 시스템은 다시 검사하지 않음
                    if system_id in system_status and system_status[system_id] is False:
                        continue
                        
                    # 오류가 있는지 확인
                    has_error = False
                    for result in system.get('inspection_results', []):
                        status_code = result.get('status_code', 0)
                        if status_code < 200 or status_code >= 400:
                            has_error = True
                            break
                    
                    # 시스템의 상태 기록 (True: 정상, False: 오류)
                    system_status[system_id] = not has_error
            else:
                # 오래된 형식: 직접 inspection_results 필드가 있는 경우
                system_id = inspection_data.get('system_id')
                if not system_id:
                    continue
                    
                # 이미 오류로 표시된 시스템은 다시 검사하지 않음
                if system_id in system_status and system_status[system_id] is False:
                    continue
                
                inspection_results = inspection_data.get('inspection_results', [])
                
                # 오류가 있는지 확인
                has_error = False
                for result in inspection_results:
                    status_code = result.get('status_code', 0)
                    if status_code < 200 or status_code >= 400:
                        has_error = True
                        break
                
                # 시스템의 상태 기록 (True: 정상, False: 오류)
                system_status[system_id] = not has_error
        
        # 최종 시스템 상태 집계
        for is_normal in system_status.values():
            if is_normal:
                today_success_count += 1
            else:
                today_error_count += 1
        
        # 이번 달 점검 내역 수집
        month_inspections = []
        
        for inspection in all_inspections:
            inspection_data = inspection.to_dict()
            # created_at 또는 inspection_start 필드 사용 (하위 호환성)
            date_field = inspection_data.get('created_at') or inspection_data.get('inspection_start')
            
            # 날짜 필드가 없는 경우 스킵
            if not date_field:
                continue
            
            # 날짜 형식에 따라 처리
            is_this_month = False
            
            # 1. 문자열인 경우
            if isinstance(date_field, str):
                is_this_month = date_field.startswith(this_month_str)
            
            # 2. datetime 객체인 경우
            elif isinstance(date_field, datetime):
                is_this_month = date_field.strftime('%Y-%m') == this_month_str
            
            # 3. timestamp 객체인 경우 (Firestore 타임스탬프)
            elif hasattr(date_field, 'timestamp'):
                # Firestore Timestamp를 datetime으로 변환
                dt = date_field.timestamp()
                is_this_month = datetime.fromtimestamp(dt).strftime('%Y-%m') == this_month_str
            
            if is_this_month:
                month_inspections.append(inspection)
        
        month_count = len(month_inspections)
        logger.info(f"이번 달 점검 횟수: {month_count}")
        
        # 결과 반환
        result = {
            "today_inspection_count": today_count,
            "today_success_system_count": today_success_count,
            "today_error_system_count": today_error_count,
            "month_inspection_count": month_count
        }
        
        logger.info(f"대시보드 통계 조회 결과: {result}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"대시보드 통계 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대시보드 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )
