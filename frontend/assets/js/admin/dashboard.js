/**
 * dashboard.js
 * 대시보드 기능 처리
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('대시보드 초기화');
    
    // 인증 확인
    checkAuth();
    
    // 이벤트 리스너 등록
    document.getElementById('addUrlBtn').addEventListener('click', showAddUrlModal);
    document.getElementById('refreshUrlsBtn').addEventListener('click', loadUrlData);
    document.getElementById('saveUrlBtn').addEventListener('click', saveUrl);
    
    // 초기 데이터 로드
    loadUrlData();
    
    /**
     * 인증 확인 및 사용자 정보 표시
     */
    function checkAuth() {
        const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
        
        if (!token) {
            // 로그인되지 않았으면 로그인 페이지로 이동
            window.location.href = '../../view/auth/signin.html';
            return;
        }
        
        // 사용자 정보 표시
        const userName = localStorage.getItem('user_name');
        if (userName) {
            // 사이드바나 네비게이션에 사용자 이름 표시
            const userNameElements = document.querySelectorAll('.user-name');
            userNameElements.forEach(el => {
                el.textContent = userName;
            });
        }
    }
    
    /**
     * URL 데이터 로드
     */
    function loadUrlData() {
        // 로딩 표시
        document.getElementById('urlTableBody').innerHTML = '<tr><td colspan="5" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">로딩 중...</span></div></td></tr>';
        
        // API 호출 예제 (실제 API가 구현되면 대체)
        setTimeout(() => {
            // 임시 데이터 - 실제로는 백엔드 API에서 가져올 것
            const mockData = [
                { id: 1, url: 'https://www.google.com', status: 'active', responseTime: '120ms', lastChecked: '2023-04-14 14:23:45' },
                { id: 2, url: 'https://www.naver.com', status: 'active', responseTime: '85ms', lastChecked: '2023-04-14 14:23:45' },
                { id: 3, url: 'https://invalid-example.com', status: 'error', responseTime: '-', lastChecked: '2023-04-14 14:23:45' },
                { id: 4, url: 'https://slow-response.com', status: 'warning', responseTime: '2340ms', lastChecked: '2023-04-14 14:23:45' },
            ];
            
            updateDashboardStats(mockData);
            renderUrlTable(mockData);
        }, 1000);
        
        // 실제 API 호출은 다음과 같이 구현할 수 있습니다
        /*
        const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
        
        axios.get('http://localhost:8000/api/urls', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            const data = response.data;
            updateDashboardStats(data);
            renderUrlTable(data);
        })
        .catch(error => {
            console.error('URL 데이터 로드 실패:', error);
            
            if (error.response && error.response.status === 401) {
                // 인증 만료, 로그인 페이지로 이동
                alert('세션이 만료되었습니다. 다시 로그인해주세요.');
                window.location.href = '../../view/auth/signin.html';
            } else {
                document.getElementById('urlTableBody').innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center text-danger">
                            데이터를 로드하는 중 오류가 발생했습니다.<br>
                            <button class="btn btn-sm btn-outline-primary mt-2" onclick="loadUrlData()">
                                다시 시도
                            </button>
                        </td>
                    </tr>
                `;
            }
        });
        */
    }
    
    /**
     * 대시보드 통계 업데이트
     */
    function updateDashboardStats(data) {
        const totalUrls = data.length;
        const activeUrls = data.filter(url => url.status === 'active').length;
        const warningUrls = data.filter(url => url.status === 'warning').length;
        const errorUrls = data.filter(url => url.status === 'error').length;
        
        document.getElementById('totalUrls').textContent = totalUrls;
        document.getElementById('activeUrls').textContent = activeUrls;
        document.getElementById('warningUrls').textContent = warningUrls;
        document.getElementById('errorUrls').textContent = errorUrls;
        
        // 퍼센트 계산 (총 URL이 0개면 0%로 표시)
        const activePercent = totalUrls ? Math.round((activeUrls / totalUrls) * 100) : 0;
        const warningPercent = totalUrls ? Math.round((warningUrls / totalUrls) * 100) : 0;
        const errorPercent = totalUrls ? Math.round((errorUrls / totalUrls) * 100) : 0;
        
        document.getElementById('activeUrlsPercent').textContent = `${activePercent}%`;
        document.getElementById('warningUrlsPercent').textContent = `${warningPercent}%`;
        document.getElementById('errorUrlsPercent').textContent = `${errorPercent}%`;
        
        // 신규 URL 퍼센트 (임시)
        document.getElementById('newUrlsPercent').textContent = '+5%';
    }
    
    /**
     * URL 테이블 렌더링
     */
    function renderUrlTable(data) {
        if (!data || data.length === 0) {
            document.getElementById('urlTableBody').innerHTML = `
                <tr>
                    <td colspan="5" class="text-center">
                        등록된 URL이 없습니다.<br>
                        <button class="btn btn-sm btn-success mt-2" id="noDataAddUrlBtn">
                            URL 추가
                        </button>
                    </td>
                </tr>
            `;
            // 버튼 이벤트 추가
            document.getElementById('noDataAddUrlBtn').addEventListener('click', showAddUrlModal);
            return;
        }
        
        let tableHtml = '';
        
        data.forEach(url => {
            const statusClass = getStatusClass(url.status);
            const statusText = getStatusText(url.status);
            
            tableHtml += `
                <tr>
                    <td>
                        <div class="d-flex px-2 py-1">
                            <div class="d-flex flex-column justify-content-center">
                                <h6 class="mb-0 text-sm">${url.url}</h6>
                                <p class="text-xs text-secondary mb-0">${url.description || ''}</p>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="badge badge-sm ${statusClass}">${statusText}</span>
                    </td>
                    <td class="align-middle text-center text-sm">
                        <span class="text-xs font-weight-bold">${url.responseTime}</span>
                    </td>
                    <td class="align-middle text-center">
                        <span class="text-xs font-weight-bold">${url.lastChecked}</span>
                    </td>
                    <td class="align-middle text-center">
                        <button class="btn btn-link text-info mb-0" 
                                onclick="checkUrl('${url.id}')" 
                                title="지금 확인">
                            <i class="material-icons">refresh</i>
                        </button>
                        <button class="btn btn-link text-warning mb-0" 
                                onclick="editUrl('${url.id}')" 
                                title="편집">
                            <i class="material-icons">edit</i>
                        </button>
                        <button class="btn btn-link text-danger mb-0" 
                                onclick="deleteUrl('${url.id}')" 
                                title="삭제">
                            <i class="material-icons">delete</i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        document.getElementById('urlTableBody').innerHTML = tableHtml;
    }
    
    /**
     * URL 추가 모달 표시
     */
    function showAddUrlModal() {
        // 모달 초기화
        document.getElementById('urlInput').value = '';
        document.getElementById('urlDescription').value = '';
        document.getElementById('urlActive').checked = true;
        
        // 모달 표시 (Bootstrap Modal)
        const modal = new bootstrap.Modal(document.getElementById('addUrlModal'));
        modal.show();
    }
    
    /**
     * URL 저장
     */
    function saveUrl() {
        const urlInput = document.getElementById('urlInput');
        const url = urlInput.value.trim();
        
        if (!url) {
            alert('URL을 입력해주세요.');
            urlInput.focus();
            return;
        }
        
        // URL 형식 검증
        if (!isValidUrl(url)) {
            alert('유효한 URL 형식이 아닙니다. (예: https://example.com)');
            urlInput.focus();
            return;
        }
        
        const description = document.getElementById('urlDescription').value.trim();
        const active = document.getElementById('urlActive').checked;
        
        // 저장 버튼 비활성화 및 로딩 표시
        const saveBtn = document.getElementById('saveUrlBtn');
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 저장 중...';
        
        // 실제 API 호출 구현 필요 (여기서는 임시로 성공 처리)
        setTimeout(() => {
            // 저장 성공 가정
            alert('URL이 저장되었습니다.');
            
            // 모달 닫기
            const modal = bootstrap.Modal.getInstance(document.getElementById('addUrlModal'));
            modal.hide();
            
            // 데이터 다시 로드
            loadUrlData();
            
            // 버튼 복원
            saveBtn.disabled = false;
            saveBtn.textContent = '저장';
        }, 1000);
    }
    
    /**
     * URL 유효성 검사
     */
    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }
    
    /**
     * 상태 클래스 반환
     */
    function getStatusClass(status) {
        switch (status) {
            case 'active':
                return 'bg-gradient-success';
            case 'warning':
                return 'bg-gradient-warning';
            case 'error':
                return 'bg-gradient-danger';
            default:
                return 'bg-gradient-secondary';
        }
    }
    
    /**
     * 상태 텍스트 반환
     */
    function getStatusText(status) {
        switch (status) {
            case 'active':
                return '정상';
            case 'warning':
                return '주의';
            case 'error':
                return '오류';
            default:
                return '알 수 없음';
        }
    }
    
    // 전역 함수 정의 (URL 작업용)
    window.checkUrl = function(id) {
        alert(`URL ID: ${id} 확인 요청`);
        // 실제 구현 필요
    };
    
    window.editUrl = function(id) {
        alert(`URL ID: ${id} 편집`);
        // 실제 구현 필요
    };
    
    window.deleteUrl = function(id) {
        if (confirm('이 URL을 삭제하시겠습니까?')) {
            alert(`URL ID: ${id} 삭제 요청`);
            // 실제 구현 필요
        }
    };
});