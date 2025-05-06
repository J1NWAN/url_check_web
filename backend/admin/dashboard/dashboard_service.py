import logging
from datetime import datetime, timedelta
from config.database import get_db
from fastapi import HTTPException, status
import json

# 로거 설정
logger = logging.getLogger(__name__)

# 타임존 정보가 있는 날짜를 타임존 정보가 없는 날짜로 변환하는 함수
def normalize_datetime(dt):
    if dt and hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

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
        
        # 시스템 컬렉션 참조
        systems_ref = db.collection('systems')
        
        # 모든 시스템 데이터 가져오기
        all_systems = list(systems_ref.get())
        
        # 등록된 시스템 수 및 이름 목록
        system_names = []
        system_data = {}
        
        for system in all_systems:
            system_dict = system.to_dict()
            system_id = system.id
            
            # 시스템 이름(한글명, 영문명)
            system_name = system_dict.get('kor_name') or system_dict.get('eng_name') or system_id
            system_names.append(system_name)
            
            # 시스템 데이터 저장
            system_data[system_id] = {
                'name': system_name,
                'latest_status': None,  # 아직 점검 결과가 없음
                'success_count': 0,
                'error_count': 0
            }
        
        logger.info(f"등록된 시스템 수: {len(system_names)}")
        
        # 점검 이력 컬렉션에서 모든 문서 가져오기
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
        
        # 각 시스템별 최신 점검 결과 찾기
        latest_inspections = {}  # 시스템별 최신 점검 기록 (system_id -> inspection)
        latest_dates = {}  # 시스템별 최신 점검 날짜 (system_id -> datetime)
        
        for inspection in all_inspections:
            inspection_data = inspection.to_dict()
            
            # 날짜 필드 확인
            date_field = inspection_data.get('created_at') or inspection_data.get('inspection_start')
            if not date_field:
                continue
                
            # 날짜 객체 얻기
            inspection_datetime = None
            
            # 1. 문자열인 경우
            if isinstance(date_field, str):
                try:
                    inspection_datetime = datetime.fromisoformat(date_field)
                except ValueError:
                    continue
            
            # 2. datetime 객체인 경우
            elif isinstance(date_field, datetime):
                inspection_datetime = date_field
            
            # 3. timestamp 객체인 경우 (Firestore 타임스탬프)
            elif hasattr(date_field, 'timestamp'):
                dt = date_field.timestamp()
                inspection_datetime = datetime.fromtimestamp(dt)
            
            # 타임존 정보 제거
            inspection_datetime = normalize_datetime(inspection_datetime)
            
            # inspection_systems 배열이 있는 경우 처리
            if 'inspection_systems' in inspection_data:
                for system in inspection_data['inspection_systems']:
                    system_id = system.get('system_id')
                    if not system_id:
                        continue
                    
                    # 해당 시스템이 데이터베이스에 등록되어 있는지 확인
                    if system_id not in system_data:
                        continue
                    
                    # 기존 최신 점검 날짜와 비교
                    if system_id not in latest_dates or inspection_datetime > latest_dates[system_id]:
                        latest_dates[system_id] = inspection_datetime
                        latest_inspections[system_id] = system
            else:
                # 오래된 형식: 직접 system_id 필드가 있는 경우
                system_id = inspection_data.get('system_id')
                if not system_id or system_id not in system_data:
                    continue
                
                # 기존 최신 점검 날짜와 비교
                if system_id not in latest_dates or inspection_datetime > latest_dates[system_id]:
                    latest_dates[system_id] = inspection_datetime
                    latest_inspections[system_id] = inspection_data
        
        # 각 시스템의 최신 상태 분석
        success_count = 0
        error_count = 0
        
        # 시스템별 결과 기록 및 최신 점검 일시 저장
        system_latest_datetime = {}
        
        for system_id, inspection in latest_inspections.items():
            # 시스템의 최신 점검 일시 저장
            inspection_datetime = latest_dates[system_id]
            formatted_datetime = inspection_datetime.strftime('%Y-%m-%d %H시 %M분 %S초')
            system_latest_datetime[system_id] = formatted_datetime
            
            # 메뉴별 성공/실패 카운트 초기화
            success_count = 0
            error_count = 0
            
            # 새로운 형식 (inspection_systems 배열 내 시스템)
            if 'inspection_results' in inspection:
                # 각 메뉴(URL)별 결과 분석
                for result in inspection['inspection_results']:
                    status_code = result.get('status_code', 0)
                    if status_code >= 200 and status_code < 400:
                        success_count += 1
                    else:
                        error_count += 1
                
                # 시스템 상태 업데이트 (메뉴별 정상/오류 카운트)
                system_data[system_id]['latest_status'] = (error_count == 0)
                system_data[system_id]['success_count'] = success_count
                system_data[system_id]['error_count'] = error_count
                system_data[system_id]['latest_datetime'] = formatted_datetime
            else:
                # 오류 데이터로 간주
                system_data[system_id]['latest_status'] = False
                system_data[system_id]['success_count'] = 0
                system_data[system_id]['error_count'] = 1
                system_data[system_id]['latest_datetime'] = formatted_datetime
        
        # 시스템별 최신 통계 데이터 구성
        system_stats = {
            "labels": system_names,
            "success_data": [system_data[system_id]['success_count'] for system_id in system_data],
            "error_data": [system_data[system_id]['error_count'] for system_id in system_data],
            "latest_datetime": [system_data[system_id].get('latest_datetime', '') for system_id in system_data]
        }
        
        # 오늘 날짜 계산 (로컬 시간 기준, 타임존 정보 없음)
        today_local = datetime.now()
        today_str = today_local.strftime('%Y-%m-%d')
        logger.info(f"오늘 날짜 문자열: {today_str}")
        
        # 이번 달 문자열
        this_month_str = today_local.strftime('%Y-%m')
        logger.info(f"이번 달 문자열: {this_month_str}")
        
        # 이번 주 시작일(일요일)과 종료일(토요일) 계산
        current_weekday = today_local.weekday()  # 0: 월요일, 1: 화요일, ..., 6: 일요일
        sunday_offset = (current_weekday + 1) % 7  # 일요일까지의 차이
        
        # 이번 주 일요일 계산
        week_start = today_local - timedelta(days=sunday_offset)
        week_start = datetime(week_start.year, week_start.month, week_start.day, 0, 0, 0)
        
        # 이번 주 토요일 계산 (일요일 + 6일)
        week_end = week_start + timedelta(days=6)
        week_end = datetime(week_end.year, week_end.month, week_end.day, 23, 59, 59)
        
        logger.info(f"이번 주 범위: {week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')}")
        
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
            
            # 날짜 객체 얻기
            inspection_datetime = None
            
            # 1. 문자열인 경우
            if isinstance(date_field, str):
                try:
                    inspection_datetime = datetime.fromisoformat(date_field)
                except ValueError:
                    # ISO 형식이 아닌 경우 스킵
                    continue
            
            # 2. datetime 객체인 경우
            elif isinstance(date_field, datetime):
                inspection_datetime = date_field
            
            # 3. timestamp 객체인 경우 (Firestore 타임스탬프)
            elif hasattr(date_field, 'timestamp'):
                # Firestore Timestamp를 datetime으로 변환
                dt = date_field.timestamp()
                inspection_datetime = datetime.fromtimestamp(dt)
            
            # 타임존 정보 제거
            inspection_datetime = normalize_datetime(inspection_datetime)
            
            # 오늘 날짜인지 확인
            is_today = inspection_datetime.strftime('%Y-%m-%d') == today_str
            
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
            
            # 날짜 객체 얻기
            inspection_datetime = None
            
            # 1. 문자열인 경우
            if isinstance(date_field, str):
                try:
                    inspection_datetime = datetime.fromisoformat(date_field)
                except ValueError:
                    # ISO 형식이 아닌 경우 스킵
                    continue
            
            # 2. datetime 객체인 경우
            elif isinstance(date_field, datetime):
                inspection_datetime = date_field
            
            # 3. timestamp 객체인 경우 (Firestore 타임스탬프)
            elif hasattr(date_field, 'timestamp'):
                # Firestore Timestamp를 datetime으로 변환
                dt = date_field.timestamp()
                inspection_datetime = datetime.fromtimestamp(dt)
            
            # 타임존 정보 제거
            inspection_datetime = normalize_datetime(inspection_datetime)
            
            # 이번 달인지 확인
            is_this_month = inspection_datetime.strftime('%Y-%m') == this_month_str
            
            if is_this_month:
                month_inspections.append(inspection)
        
        month_count = len(month_inspections)
        logger.info(f"이번 달 점검 횟수: {month_count}")
        
        # 이번 주 점검 데이터 수집 (요일별)
        weekly_data = {
            0: {"total": 0, "success": 0, "error": 0},  # 일요일
            1: {"total": 0, "success": 0, "error": 0},  # 월요일
            2: {"total": 0, "success": 0, "error": 0},  # 화요일
            3: {"total": 0, "success": 0, "error": 0},  # 수요일
            4: {"total": 0, "success": 0, "error": 0},  # 목요일
            5: {"total": 0, "success": 0, "error": 0},  # 금요일
            6: {"total": 0, "success": 0, "error": 0},  # 토요일
        }
        
        # 올해 월별 점검 횟수 통계 데이터
        current_year = today_local.year
        monthly_data = {
            1: 0,   # 1월
            2: 0,   # 2월
            3: 0,   # 3월
            4: 0,   # 4월
            5: 0,   # 5월
            6: 0,   # 6월
            7: 0,   # 7월
            8: 0,   # 8월
            9: 0,   # 9월
            10: 0,  # 10월
            11: 0,  # 11월
            12: 0   # 12월
        }
        
        # 요일별 점검 개수 및 정상/오류 개수 계산
        for inspection in all_inspections:
            inspection_data = inspection.to_dict()
            # created_at 또는 inspection_start 필드 사용 (하위 호환성)
            date_field = inspection_data.get('created_at') or inspection_data.get('inspection_start')
            
            # 날짜 필드가 없는 경우 스킵
            if not date_field:
                continue
            
            # 이번 주 데이터인지 확인
            inspection_datetime = None
            
            # 1. 문자열인 경우 (ISO 형식 문자열 가정)
            if isinstance(date_field, str):
                try:
                    inspection_datetime = datetime.fromisoformat(date_field)
                except ValueError:
                    # ISO 형식이 아닌 경우 스킵
                    continue
            
            # 2. datetime 객체인 경우
            elif isinstance(date_field, datetime):
                inspection_datetime = date_field
            
            # 3. timestamp 객체인 경우 (Firestore 타임스탬프)
            elif hasattr(date_field, 'timestamp'):
                # Firestore Timestamp를 datetime으로 변환
                dt = date_field.timestamp()
                inspection_datetime = datetime.fromtimestamp(dt)
            
            # 날짜 필드가 없는 경우 스킵
            if not inspection_datetime:
                continue
                
            # 타임존 정보 제거
            inspection_datetime = normalize_datetime(inspection_datetime)
            
            # 이번 주 범위에 해당하는지 확인
            if week_start <= inspection_datetime <= week_end:
                # 요일 구하기 (0: 월요일 -> 6: 일요일, 변환: 0: 일요일 -> 6: 토요일)
                weekday = (inspection_datetime.weekday() + 1) % 7
                
                # 총 점검 횟수 증가
                weekly_data[weekday]["total"] += 1
                
                # 시스템 상태 분석
                if 'inspection_systems' in inspection_data:
                    for system in inspection_data['inspection_systems']:
                        # 오류가 있는지 확인
                        has_error = False
                        for result in system.get('inspection_results', []):
                            status_code = result.get('status_code', 0)
                            if status_code < 200 or status_code >= 400:
                                has_error = True
                                break
                        
                        if has_error:
                            weekly_data[weekday]["error"] += 1
                        else:
                            weekly_data[weekday]["success"] += 1
                else:
                    # 오래된 형식: 직접 inspection_results 필드가 있는 경우
                    inspection_results = inspection_data.get('inspection_results', [])
                    
                    has_error = False
                    for result in inspection_results:
                        status_code = result.get('status_code', 0)
                        if status_code < 200 or status_code >= 400:
                            has_error = True
                            break
                    
                    if has_error:
                        weekly_data[weekday]["error"] += 1
                    else:
                        weekly_data[weekday]["success"] += 1
            
            # 올해 데이터인지 확인하여 월별 통계 추가
            if inspection_datetime.year == current_year:
                month = inspection_datetime.month
                
                # 점검 횟수 증가
                if 'inspection_systems' in inspection_data:
                    # 여러 시스템이 있는 경우 각 시스템을 개별적으로 카운트
                    monthly_data[month] += len(inspection_data['inspection_systems'])
                else:
                    # 단일 시스템 점검인 경우
                    monthly_data[month] += 1
        
        # 결과 반환
        result = {
            "today_inspection_count": today_count,
            "today_success_system_count": today_success_count,
            "today_error_system_count": today_error_count,
            "month_inspection_count": month_count,
            # 시스템별 최신 통계 데이터 추가
            "system_stats": system_stats,
            # 이번 주 점검 통계 데이터 추가
            "weekly_inspection_stats": {
                "labels": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                "success_data": [
                    weekly_data[0]["success"],
                    weekly_data[1]["success"],
                    weekly_data[2]["success"],
                    weekly_data[3]["success"],
                    weekly_data[4]["success"],
                    weekly_data[5]["success"],
                    weekly_data[6]["success"]
                ],
                "error_data": [
                    weekly_data[0]["error"],
                    weekly_data[1]["error"],
                    weekly_data[2]["error"],
                    weekly_data[3]["error"],
                    weekly_data[4]["error"],
                    weekly_data[5]["error"],
                    weekly_data[6]["error"]
                ],
                "total_data": [
                    weekly_data[0]["total"],
                    weekly_data[1]["total"],
                    weekly_data[2]["total"],
                    weekly_data[3]["total"],
                    weekly_data[4]["total"],
                    weekly_data[5]["total"],
                    weekly_data[6]["total"]
                ]
            },
            # 올해 월별 점검 횟수 통계 추가
            "yearly_inspection_stats": {
                "year": current_year,
                "labels": ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"],
                "data": [
                    monthly_data[1],
                    monthly_data[2],
                    monthly_data[3],
                    monthly_data[4],
                    monthly_data[5],
                    monthly_data[6],
                    monthly_data[7],
                    monthly_data[8],
                    monthly_data[9],
                    monthly_data[10],
                    monthly_data[11],
                    monthly_data[12]
                ]
            }
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
