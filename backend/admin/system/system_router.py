from fastapi import APIRouter, HTTPException, Request, status, Path
from fastapi.responses import JSONResponse
import logging
from typing import List

from config.templates import templates
from .system_model import SystemCreate, SystemResponse, SystemUpdate
from .system_service import create_system, get_systems, get_system, update_system, delete_system

# 로거 설정
logger = logging.getLogger(__name__)

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