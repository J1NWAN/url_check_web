from fastapi import APIRouter, HTTPException, Request, status, Path, Query, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from util.util import verify_token
import logging
from typing import List, Optional, Dict, Any
import aiohttp
import asyncio
import time
from datetime import datetime

from config.templates import templates
from config.database import get_db
from .system_model import SystemCreate, SystemResponse, SystemUpdate, SystemInspectionResponse
from .system_service import (
    create_system, get_systems, get_system, update_system, delete_system, 
    inspect_system, get_system_inspections, perform_system_inspection, 
    save_inspection_history, get_recent_inspections, get_system_detail
)
from history.history_service import get_system_statistics, get_latest_inspection_result

# 로거 설정
logger = logging.getLogger(__name__)

# 토큰 인증 의존성
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# 라우터 정의
router = APIRouter(tags=["시스템"])

# 시스템 페이지
@router.get("/admin/system")
async def admin_system(request: Request):
    return templates.TemplateResponse("admin/system.html", {"request": request})

# 시스템 생성 API
@router.post("/api/systems", response_model=SystemResponse, status_code=status.HTTP_201_CREATED)
async def create_system_api(system_data: SystemCreate):
    try:
        return await create_system(system_data)
    except Exception as e:
        logger.error(f"시스템 생성 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 생성 중 오류가 발생했습니다: {str(e)}"
        )

# 모든 시스템 조회 API
@router.get("/api/systems", response_model=List[SystemResponse])
async def get_systems_api():
    try:
        return await get_systems()
    except Exception as e:
        logger.error(f"시스템 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

# 특정 시스템 조회 API
@router.get("/api/systems/{system_id}", response_model=SystemResponse)
async def get_system_api(system_id: str = Path(..., description="조회할 시스템 ID")):
    try:
        system = await get_system(system_id)
        if not system:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {system_id}인 시스템을 찾을 수 없습니다."
            )
        return system
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 조회 중 오류가 발생했습니다: {str(e)}"
        )

# 시스템 업데이트 API
@router.put("/api/systems/{system_id}", response_model=SystemResponse)
async def update_system_api(
    system_data: SystemUpdate,
    system_id: str = Path(..., description="업데이트할 시스템 ID")
):
    try:
        return await update_system(system_id, system_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 업데이트 중 오류가 발생했습니다: {str(e)}"
        )

# 시스템 삭제 API
@router.delete("/api/systems/{system_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_system_api(system_id: str = Path(..., description="삭제할 시스템 ID")):
    try:
        result = await delete_system(system_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {system_id}인 시스템을 찾을 수 없습니다."
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 삭제 중 오류가 발생했습니다: {str(e)}"
        )

# 시스템 점검 API
@router.post("/api/systems/{system_id}/inspect", response_model=SystemInspectionResponse)
async def inspect_system_api(
    request: Request,
    system_id: str = Path(..., description="점검할 시스템 ID"),
    inspection_type: str = Query("자동", description="점검 유형 (자동 또는 수동)"),
    authorization: Optional[str] = Header(None, description="Authorization header")
):
    try:
        # 요청 본문에서 사용자의 userid와 점검 유형 가져오기
        req_body = await request.json()
        userid = req_body.get("inspected_by", "system")
        
        # 요청 본문에서 점검 유형 가져오기 (요청 본문의 값이 있으면 우선 사용)
        req_inspection_type = req_body.get("inspection_type")
        if req_inspection_type:
            inspection_type = req_inspection_type
        
        # 빈 문자열이나 None인 경우 기본값 사용
        if not userid:
            userid = "system"
        
        # 점검 유형 유효성 검사
        if inspection_type not in ["자동", "수동"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="점검 유형은 '자동' 또는 '수동'이어야 합니다."
            )
        
        # 수동 점검인 경우 사용자가 제공한 메뉴 결과 확인
        inspection_results = req_body.get("inspection_results")
        
        logger.info(f"시스템 점검 요청: 시스템ID={system_id}, 유형={inspection_type}, 사용자={userid}, 메뉴결과={inspection_results}")
        return await inspect_system(system_id, inspection_type, userid, inspection_results)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 점검 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 점검 중 오류가 발생했습니다: {str(e)}"
        )

# 시스템 점검 이력 조회 API
@router.get("/api/systems/{system_id}/inspections", response_model=List[SystemInspectionResponse])
async def get_system_inspections_api(
    system_id: str = Path(..., description="점검 이력을 조회할 시스템 ID"),
    limit: int = Query(10, description="조회할 이력 개수", ge=1, le=100)
):
    try:
        return await get_system_inspections(system_id, limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 점검 이력 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"시스템 점검 이력 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/api/proxy-header")
async def proxy_header(request: Request):
    """특정 URL의 헤더 정보를 가져오는 프록시 API"""
    try:
        # 요청 본문에서 URL 가져오기
        req_body = await request.json()
        url = req_body.get("url")
        
        if not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL이 제공되지 않았습니다."
            )
        
        logger.info(f"헤더 정보 요청: URL={url}")
        
        # 타임아웃 설정으로 빠른 응답 보장
        timeout = aiohttp.ClientTimeout(total=5)
        start_time = time.time()
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                # HEAD 요청으로 헤더 정보 얻기
                async with session.head(url) as head_response:
                    end_time = time.time()
                    response_time = round((end_time - start_time) * 1000, 2)  # ms 단위로 변환
                    
                    # 응답 헤더 가져오기
                    headers = dict(head_response.headers)
                    # 헤더값을 문자열로 변환 (자동 검사의 형식과 동일하게)
                    headers = {k: str(v) for k, v in headers.items()}
                    
                    # HEAD 요청이 성공하면 해당 결과 반환
                    if head_response.status < 400:
                        return {
                            "url": url,
                            "status_code": head_response.status,
                            "headers": headers,
                            "responseTime": response_time
                        }
                
                # HEAD 요청이 실패하면(4xx, 5xx 응답) GET 요청 시도
                start_time = time.time()
                async with session.get(url, allow_redirects=True) as get_response:
                    end_time = time.time()
                    response_time = round((end_time - start_time) * 1000, 2)
                    
                    # 응답 헤더 가져오기
                    headers = dict(get_response.headers)
                    # 헤더값을 문자열로 변환 (자동 검사의 형식과 동일하게)
                    headers = {k: str(v) for k, v in headers.items()}
                    
                    return {
                        "url": url,
                        "status_code": get_response.status,
                        "headers": headers,
                        "responseTime": response_time
                    }
            except asyncio.TimeoutError:
                logger.warning(f"요청 타임아웃: {url}")
                return {
                    "url": url,
                    "status_code": 408,
                    "headers": {},
                    "responseTime": 5000  # 5초 타임아웃
                }
            except Exception as e:
                logger.error(f"헤더 정보 가져오기 실패: {url}, 오류: {str(e)}")
                return {
                    "url": url,
                    "status_code": 0,
                    "headers": {},
                    "responseTime": 0,
                    "error": str(e)
                }
    except Exception as e:
        logger.error(f"프록시 헤더 API 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"헤더 정보를 가져오는 중 오류가 발생했습니다: {str(e)}"
        )

# 전체 시스템 점검 API
@router.post("/api/systems/inspect-all", response_model=List[SystemInspectionResponse])
async def inspect_all_systems_api(request: Request):
    """모든 시스템을 일괄 점검하는 API"""
    try:
        # 요청 본문에서 사용자의 userid 가져오기
        req_body = await request.json()
        userid = req_body.get("inspected_by", "system")
        
        # 빈 문자열이나 None인 경우 기본값 사용
        if not userid:
            userid = "system"
        
        # 모든 시스템 목록 조회
        systems = await get_systems()
        
        if not systems:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="등록된 시스템이 없습니다."
            )
        
        # 점검 시간으로 문서 이름 생성 (YYYYMMDDHI24MISS 형식)
        document_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 점검 결과를 저장할 배열
        inspection_systems = []
        inspection_responses = []
        
        # 각 시스템 순차적으로 점검
        for system in systems:
            try:
                # 개별 시스템 점검 수행 (저장은 하지 않고 결과만 가져옴)
                inspection_data = await perform_system_inspection(system.id, "자동", userid)
                
                # 결과 배열에 추가
                inspection_systems.append(inspection_data)
                
                # 응답용 객체 생성
                for date_field in ['inspection_start', 'inspection_end']:
                    if isinstance(inspection_data.get(date_field), str):
                        inspection_data[date_field] = datetime.fromisoformat(inspection_data[date_field])
                
                inspection_responses.append(SystemInspectionResponse(**inspection_data))
            except Exception as e:
                logger.error(f"시스템 점검 중 오류 발생 (ID: {system.id}): {str(e)}")
                # 오류가 발생해도 계속 진행
                continue
        
        # 모든 시스템 점검 결과를 하나의 문서로 저장
        if inspection_systems:
            await save_inspection_history(inspection_systems, document_id)
        
        return inspection_responses
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"전체 시스템 점검 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"전체 시스템 점검 중 오류가 발생했습니다: {str(e)}"
        )

# 최근 점검 이력 조회 API
@router.get("/api/inspections/recent", response_model=List[Dict[str, Any]])
async def get_recent_inspections_api(
    limit: int = Query(5, description="조회할 이력 개수", ge=1, le=10)
):
    """최근 점검 이력을 조회하는 API"""
    try:
        return await get_recent_inspections(limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"최근 점검 이력 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"최근 점검 이력 조회 중 오류가 발생했습니다: {str(e)}"
        )

# 시스템 상세 정보 API
@router.get("/api/system/{system_id}", tags=["시스템 관리 API"])
async def get_system_detail_api(system_id: str, token: str = Depends(oauth2_scheme)):
    """시스템의 상세 정보를 가져옵니다."""
    try:
        # 토큰 검증
        verify_result = verify_token(token)
        if not verify_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 유효하지 않습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 시스템 ID 검증
        if not system_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="시스템 ID가 필요합니다"
            )
        
        # 시스템 정보 가져오기 (service 모듈의 함수 호출)
        from .system_service import get_system_detail
        system_info = await get_system_detail(system_id)
        
        if not system_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"시스템을 찾을 수 없습니다 (ID: {system_id})"
            )
        
        # 점검 통계 정보 가져오기 (히스토리 모듈에서 가져옴)
        statistics = await get_system_statistics(system_id)
        latest_inspection = await get_latest_inspection_result(system_id)
        
        # 응답 데이터 구성
        response_data = {
            "id": system_id,
            "name": system_info.get("name", ""),
            "description": system_info.get("description", ""),
            "url": system_info.get("url", ""),
            "menus": system_info.get("menus", []),
            "created_at": system_info.get("created_at", ""),
            "updated_at": system_info.get("updated_at", ""),
            "statistics": {
                "total_inspections": statistics.total_inspections,
                "success_count": statistics.success_count,
                "error_count": statistics.error_count,
                "success_rate": statistics.success_rate
            }
        }
        
        # 최신 점검 결과가 있는 경우 추가
        if latest_inspection:
            response_data["latest_inspection"] = {
                "inspection_date": latest_inspection.inspection_date,
                "has_error": latest_inspection.has_error
            }
        
        return response_data
    
    except HTTPException as e:
        # HTTP 예외는 그대로 전달
        raise e
    except Exception as e:
        logger.error(f"시스템 상세 정보 API 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 오류: {str(e)}"
        )