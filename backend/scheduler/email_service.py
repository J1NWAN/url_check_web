"""
URL Check Web 이메일 서비스 모듈

시스템 점검 결과를 이메일로 발송하는 기능을 제공합니다.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
import os
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 이메일 설정 (환경 변수에서 가져오거나 기본값 사용)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@example.com")

async def send_inspection_email(recipients: List[str], inspection_systems: List[Dict[str, Any]]) -> bool:
    """
    시스템 점검 결과를 이메일로 발송합니다.
    
    Args:
        recipients: 수신자 이메일 목록
        inspection_systems: 점검 결과 데이터 목록
        
    Returns:
        bool: 발송 성공 여부
    """
    if not recipients or not inspection_systems:
        logger.warning("수신자 목록이나 점검 결과가 비어 있어 이메일을 발송하지 않습니다.")
        return False
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.error("SMTP 인증 정보가 설정되지 않았습니다. 환경 변수를 확인하세요.")
        return False
    
    try:
        # 이메일 제목 생성
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        subject = f"[URL Check Web] 시스템 점검 결과 ({now})"
        
        # HTML 본문 생성
        html_content = generate_email_html(inspection_systems)
        
        # 이메일 메시지 생성
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = EMAIL_FROM
        message["To"] = ", ".join(recipients)
        
        # HTML 본문 추가
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # SMTP 서버 연결 및 이메일 발송
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
        
        logger.info(f"점검 결과 이메일 발송 완료: {len(recipients)}명 수신자, {len(inspection_systems)}개 시스템")
        return True
        
    except Exception as e:
        logger.error(f"이메일 발송 중 오류 발생: {str(e)}")
        return False

def generate_email_html(inspection_systems: List[Dict[str, Any]]) -> str:
    """
    점검 결과를 HTML 형식으로 변환합니다.
    
    Args:
        inspection_systems: 점검 결과 데이터 목록
        
    Returns:
        str: HTML 형식의 이메일 본문
    """
    # 이메일 헤더 생성
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .container { max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
            h2 { color: #444; margin-top: 20px; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .success { color: green; }
            .error { color: red; }
            .warning { color: orange; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>시스템 점검 결과</h1>
            <p>아래는 자동화된 시스템 점검 결과입니다.</p>
    """
    
    # 각 시스템별 결과 추가
    for system in inspection_systems:
        system_name = system.get("system_kor_name", "알 수 없는 시스템")
        system_url = system.get("system_url", "")
        inspection_start = system.get("inspection_start")
        if isinstance(inspection_start, str):
            inspection_start = datetime.fromisoformat(inspection_start)
        inspection_time = inspection_start.strftime("%Y-%m-%d %H:%M:%S") if inspection_start else "알 수 없음"
        
        html += f"""
            <h2>{system_name}</h2>
            <p><strong>URL:</strong> <a href="{system_url}" target="_blank">{system_url}</a></p>
            <p><strong>점검 시간:</strong> {inspection_time}</p>
            <table>
                <tr>
                    <th>메뉴</th>
                    <th>경로</th>
                    <th>상태 코드</th>
                    <th>상태</th>
                    <th>응답 시간(ms)</th>
                </tr>
        """
        
        # 메뉴별 결과 추가
        results = system.get("inspection_results", [])
        for result in results:
            menu_name = result.get("menu_name", "")
            path = result.get("path", "")
            status_code = result.get("status_code", 0)
            status_text = result.get("status_text", "")
            response_time = result.get("response_time", 0)
            
            # 상태 코드에 따른 스타일 결정
            status_class = "success" if 200 <= status_code < 300 else "error" if status_code >= 400 else "warning"
            
            html += f"""
                <tr>
                    <td>{menu_name}</td>
                    <td>{path}</td>
                    <td>{status_code}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{response_time}</td>
                </tr>
            """
        
        html += """
            </table>
        """
    
    # 이메일 푸터 추가
    html += """
            <p>이 이메일은 자동으로 생성되었습니다. 문의사항이 있으시면 관리자에게 연락해주세요.</p>
        </div>
    </body>
    </html>
    """
    
    return html 