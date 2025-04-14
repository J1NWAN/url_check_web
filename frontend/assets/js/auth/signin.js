/**
 * signin.js
 * 로그인 폼 제출 및 인증 처리
 */
console.log('로그인 폼 초기화');

var loginForm = document.getElementById('loginForm');
var loginButton = document.getElementById('loginButton');
var loginError = document.getElementById('loginError');

// 이미 로그인되어 있는지 확인
checkAuthStatus();

// 로그인 버튼 클릭 이벤트
loginButton.addEventListener('click', function(event) {
    event.preventDefault();
    attemptLogin();
});

// 폼 엔터 키 제출 처리
loginForm.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        attemptLogin();
    }
});

/**
 * 로그인 요청 처리 함수
 */
function attemptLogin() {
    // 오류 메시지 초기화
    loginError.style.display = 'none';
    loginError.textContent = '';
    
    // 입력값 검증
    const userid = document.getElementById('userid').value.trim();
    const password = document.getElementById('password').value;
    
    if (!userid || !password) {
        showError('아이디와 비밀번호를 모두 입력해주세요.');
        return;
    }
    
    // 버튼 비활성화 및 로딩 상태 표시
    loginButton.disabled = true;
    loginButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 로그인 중...';
    
    // 로그인 API 호출
    axios.post('http://localhost:8000/api/auth/login', {
        userid: userid,
        password: password
    })
    .then(response => {
        console.log('로그인 성공:', response.data);
        
        // 토큰 및 사용자 정보 저장
        localStorage.setItem('auth_token', response.data.access_token);
        localStorage.setItem('user_id', response.data.user_id);
        localStorage.setItem('userid', response.data.userid);
        localStorage.setItem('user_name', response.data.name);
        
        // 로그인 유지 체크 시 만료 시간 설정
        if (document.getElementById('rememberMe').checked) {
            const expiry = new Date();
            expiry.setDate(expiry.getDate() + 7); // 7일 후 만료
            localStorage.setItem('token_expiry', expiry.toISOString());
        } else {
            // 브라우저 종료 시 만료 (세션 기반)
            sessionStorage.setItem('auth_token', response.data.access_token);
            // localStorage에서는 제거 (세션만 사용)
            localStorage.removeItem('token_expiry');
        }
        
        // 메인 페이지로 리다이렉트
        window.location.href = '../../index.html'; // 또는 대시보드/메인 페이지 경로
    })
    .catch(error => {
        console.error('로그인 오류:', error);
        
        let errorMessage = '로그인 처리 중 오류가 발생했습니다.';
        
        if (error.response) {
            // 서버 응답 오류
            const status = error.response.status;
            const detail = error.response.data.detail;
            
            if (status === 401) {
                errorMessage = detail || '아이디 또는 비밀번호가 올바르지 않습니다.';
            } else if (status === 500) {
                errorMessage = '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
            } else {
                errorMessage = detail || errorMessage;
            }
        } else if (error.request) {
            // 서버 연결 실패
            errorMessage = '서버에 연결할 수 없습니다. 네트워크 연결을 확인하세요.';
        }
        
        showError(errorMessage);
    })
    .finally(() => {
        // 버튼 상태 복원
        loginButton.disabled = false;
        loginButton.textContent = '로그인';
    });
}

/**
 * 오류 메시지 표시 함수
 */
function showError(message) {
    loginError.textContent = message;
    loginError.style.display = 'block';
}

/**
 * 인증 상태 확인 함수
 * 이미 로그인되어 있으면 메인 페이지로 리다이렉트
 */
function checkAuthStatus() {
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    const expiry = localStorage.getItem('token_expiry');
    
    if (token) {
        // 토큰 만료 검사
        if (expiry && new Date(expiry) < new Date()) {
            // 토큰 만료됨, 로그아웃 처리
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_id');
            localStorage.removeItem('userid');
            localStorage.removeItem('user_name');
            localStorage.removeItem('token_expiry');
            sessionStorage.removeItem('auth_token');
            return;
        }
        
        // 유효한 토큰이 있으면 메인 페이지로 리다이렉트
        window.location.href = '../../index.html'; // 또는 대시보드/메인 페이지 경로
    }
}
