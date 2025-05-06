"""
URL Check Web 스케줄러 모듈

APScheduler를 사용하여 시스템 자동 점검을 정기적으로 수행합니다.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.interval import IntervalTrigger
import os

# 스케줄러 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 시스템 점검 서비스 임포트
from admin.system.system_service import get_systems, perform_system_inspection, save_inspection_history

# 전역 스케줄러 객체
scheduler = None

async def run_system_inspection():
    """
    모든 시스템에 대한 자동 점검을 수행하고 결과를 저장하는 작업
    """
    try:
        logger.info("자동 시스템 점검 작업 시작")
        
        # 모든 시스템 목록 조회
        systems = await get_systems()
        
        if not systems:
            logger.warning("등록된 시스템이 없습니다.")
            return
        
        # 점검 시간으로 문서 이름 생성 (YYYYMMDDHI24MISS 형식)
        document_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 점검 결과를 저장할 배열
        inspection_systems = []
        
        # 각 시스템 순차적으로 점검
        for system in systems:
            try:
                # 개별 시스템 점검 수행 (저장은 하지 않고 결과만 가져옴)
                inspection_data = await perform_system_inspection(system.id, "자동", "scheduler", None)
                
                # 결과 배열에 추가
                inspection_systems.append(inspection_data)
                
                logger.info(f"시스템 '{system.kor_name}' 점검 완료")
            except Exception as e:
                logger.error(f"시스템 점검 중 오류 발생 (ID: {system.id}): {str(e)}")
                # 오류가 발생해도 계속 진행
                continue
        
        # 모든 시스템 점검 결과를 하나의 문서로 저장
        if inspection_systems:
            await save_inspection_history(inspection_systems, document_id)
            logger.info(f"자동 점검 결과 저장 완료: {len(inspection_systems)}개 시스템, 문서 ID: {document_id}")
        else:
            logger.warning("저장할 점검 결과가 없습니다.")
        
    except Exception as e:
        logger.error(f"자동 시스템 점검 작업 중 오류 발생: {str(e)}")

def initialize_scheduler():
    """
    스케줄러를 초기화하고 작업을 등록합니다.
    """
    global scheduler
    
    try:
        # 이미 스케줄러가 실행 중인 경우 중지
        if scheduler and scheduler.running:
            scheduler.shutdown()
            logger.info("기존 스케줄러 중지")
        
        # SQLAlchemy JobStore 설정
        jobstore_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scheduler", "jobs")
        os.makedirs(jobstore_dir, exist_ok=True)
        jobstore_path = os.path.join(jobstore_dir, "jobs.sqlite")
        
        # JobStore 생성
        jobstore = SQLAlchemyJobStore(url=f'sqlite:///{jobstore_path}')
        
        # 스케줄러 생성
        scheduler = AsyncIOScheduler(jobstores={'default': jobstore})
        
        # 10분마다 실행되는 시스템 점검 작업 등록
        scheduler.add_job(
            run_system_inspection,
            trigger=IntervalTrigger(minutes=10),
            id='system_inspection',
            name='시스템 자동 점검',
            replace_existing=True
        )
        
        # 스케줄러 시작
        scheduler.start()
        logger.info("스케줄러 초기화 완료: 10분마다 시스템 자동 점검")
        
        return scheduler
    except Exception as e:
        logger.error(f"스케줄러 초기화 중 오류 발생: {str(e)}")
        return None

def get_scheduler():
    """
    현재 스케줄러 인스턴스를 반환합니다.
    """
    global scheduler
    return scheduler 