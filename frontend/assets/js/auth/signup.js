/**
 * signup.js
 * 회원가입 폼 제출 및 유효성 검사 처리
 */
console.log('레이아웃 준비 완료, 회원가입 폼 초기화 시작');
    
var registerForm = document.getElementById('registerForm');
var registerButton = document.getElementById('registerButton');
var alertContainer = document.createElement('div');
alertContainer.id = 'alertContainer';
alertContainer.style.marginBottom = '1rem';
    
// 알림 컨테이너를 폼 맨 위에 추가
if (registerForm) {
    registerForm.prepend(alertContainer);
}

// 알림 메시지 표시 함수
function showAlert(message, type = 'danger') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} text-white`;
    alertDiv.innerHTML = message;
    
    alertContainer.innerHTML = '';
    alertContainer.appendChild(alertDiv);
    
    // 5초 후 알림 숨기기
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// 폼 유효성 검사
function validateForm() {
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (password !== confirmPassword) {
        showAlert('비밀번호가 일치하지 않습니다.');
        return false;
    }
    
    // 비밀번호 복잡성 검사
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    
    if (password.length < 8 || !hasUpperCase || !hasLowerCase || !hasNumbers || !hasSpecialChar) {
        showAlert('비밀번호는 8자 이상이며, 대문자, 소문자, 숫자, 특수문자를 포함해야 합니다.');
        return false;
    }
    
    return true;
}

registerButton.addEventListener('click', function(event) {
    event.preventDefault();
    console.log('버튼 클릭됨!');
    
    // axios 확인
    if (typeof axios === 'undefined') {
        console.error('axios가 로드되지 않았습니다!');
        showAlert('axios 라이브러리가 로드되지 않았습니다. 페이지를 새로고침하거나 나중에 다시 시도하세요.');
        return;
    }
    
    // 폼 유효성 검사
    if (!validateForm()) {
        return;
    }
    
    // 버튼 비활성화 및 로딩 표시
    registerButton.disabled = true;
    registerButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 처리 중...';
    
    // 폼 데이터 수집
    const formData = new FormData(registerForm);
    const userData = {
        userid: formData.get('userid'),
        name: formData.get('name'),
        email: formData.get('email'),
        password: formData.get('password'),
        password_confirm: formData.get('password_confirm')
    };
    
    console.log('전송할 데이터:', userData);
    
    // API 호출
    axios.post('http://localhost:8000/api/auth/register', userData)
        .then(response => {
            console.log('성공:', response.data);
            showAlert('회원가입이 완료되었습니다! 잠시 후 로그인 페이지로 이동합니다.', 'success');
            
            // 3초 후 로그인 페이지로 이동
            setTimeout(() => {
                window.location.href = 'signin.html';
            }, 3000);
        })
        .catch(error => {
            console.error('오류:', error);
            let errorMessage = '회원가입 중 오류가 발생했습니다.';
            
            if (error.response) {
                errorMessage = error.response.data.detail || errorMessage;
            } else if (error.request) {
                errorMessage = '서버에 연결할 수 없습니다. 네트워크 연결을 확인하세요.';
            }
            
            showAlert(errorMessage);
        })
        .finally(() => {
            // 버튼 상태 복원
            registerButton.disabled = false;
            registerButton.textContent = '등록';
        });
});