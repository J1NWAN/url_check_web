import os
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request

# 기본 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, 'view')
STATIC_DIR = os.path.join(FRONTEND_DIR, 'assets')

# 템플릿 객체 생성
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# 정적 파일 마운트 함수
def mount_static_files(app):
    app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")