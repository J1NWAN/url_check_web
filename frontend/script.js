// 백엔드 API 주소 (FastAPI 서버 주소)
const BACKEND_URL = 'http://localhost:8000'; // 로컬 개발 환경
// const BACKEND_URL = 'YOUR_RENDER_BACKEND_URL'; // Render 배포 시

// 데이터 표시 영역
const dataDiv = document.getElementById('data');

// 페이지 로드 시 데이터 가져오기
document.addEventListener('DOMContentLoaded', fetchData);

async function fetchData() {
    try {
        const response = await axios.get(`${BACKEND_URL}/`); // 루트 엔드포인트 호출 예시
        dataDiv.textContent = JSON.stringify(response.data);
    } catch (error) {
        console.error('Error fetching data:', error);
        dataDiv.textContent = '데이터를 불러오는 데 실패했습니다.';
    }
} 