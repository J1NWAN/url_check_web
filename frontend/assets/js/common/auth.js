/**
 * URL Checker - 인증 관련 공통 기능
 * 
 * 모든 관리자 페이지에서 사용할 인증 관련 기능을 제공합니다.
 * - 로그인 여부 확인
 * - 사용자 정보 가져오기
 * - 로그인/로그아웃 기능
 */

// 현재 로그인한 사용자 정보
const currentUser = {
  id: null,
  userid: null,
  name: null,
  role: null
};

/**
 * 로그인 여부 확인
 * @returns {boolean} 로그인 상태
 */
function isLoggedIn() {
  const token = localStorage.getItem('access_token');
  return token !== null && token !== undefined && token !== '';
}

/**
 * 로그아웃 처리
 * 로컬 스토리지의 토큰, 사용자 정보를 제거하고 로그인 페이지로 리디렉션합니다.
 */
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_id');
  localStorage.removeItem('userid');
  localStorage.removeItem('username');
  
  // 현재 URL을 저장하여 로그인 후 돌아올 수 있도록 함
  sessionStorage.setItem('redirect_after_login', window.location.pathname);
  
  // 로그인 페이지로 리디렉션
  window.location.href = '/auth/signin';
}

/**
 * 로그인 체크 및 리디렉션
 * 로그인되지 않았으면 로그인 페이지로 리디렉션합니다.
 * @returns {boolean} 로그인 여부
 */
function checkLoginAndRedirect() {
  if (!isLoggedIn()) {
    console.warn('로그인되지 않은 상태입니다. 로그인 페이지로 이동합니다.');
    // 현재 URL을 저장하여 로그인 후 돌아올 수 있도록 함
    sessionStorage.setItem('redirect_after_login', window.location.pathname);
    window.location.href = '/auth/signin';
    return false;
  }
  return true;
}

/**
 * 현재 로그인한 사용자 정보 가져오기
 * @returns {Promise<boolean>} 사용자 정보 가져오기 성공 여부
 */
async function fetchCurrentUser() {
  try {
    // 로컬 스토리지에서 액세스 토큰 가져오기
    const token = localStorage.getItem('access_token');
    
    // 토큰이 있으면 API 호출
    if (token) {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const userData = await response.json();
        
        // 사용자 정보 설정
        currentUser.id = userData.id;
        currentUser.userid = userData.userid;
        currentUser.name = userData.name;
        currentUser.role = userData.role || 'user';
        
        // 로컬 스토리지에 저장
        localStorage.setItem('user_id', currentUser.id);
        localStorage.setItem('userid', currentUser.userid);
        localStorage.setItem('username', currentUser.name);
        
        return true;
      } else {
        // 401 오류 등 인증 실패 시 로그아웃 처리
        if (response.status === 401) {
          console.warn('인증 토큰이 만료되었거나 유효하지 않습니다. 다시 로그인이 필요합니다.');
          logout();
          return false;
        }
      }
    }
    
    // 토큰이 없거나 API 호출 실패 시 로컬 스토리지에서 확인
    const userId = localStorage.getItem('user_id');
    const userid = localStorage.getItem('userid');
    const username = localStorage.getItem('username');
    
    if (userId && (userid || username)) {
      // 로컬 스토리지에 정보가 있는 경우
      currentUser.id = userId;
      currentUser.userid = userid || username;
      currentUser.name = username || userid;
      currentUser.role = 'user';
      console.log('로컬 스토리지에서 사용자 정보 복원:', currentUser);
      return true;
    } else {
      // 기본값 설정
      console.warn('토큰이 없거나 API 호출 실패, 기본값 사용');
      currentUser.id = 'system';
      currentUser.userid = 'system';
      currentUser.name = '시스템';
      currentUser.role = 'system';
      return false;
    }
  } catch (error) {
    console.error('Error fetching user data:', error);
    
    // 에러 발생 시 기본값 설정
    currentUser.id = 'system';
    currentUser.userid = 'system';
    currentUser.name = '시스템';
    currentUser.role = 'system';
    return false;
  }
}

/**
 * 페이지 초기화 함수
 * 사용자 정보를 가져오고 로그인 체크 및 리디렉션을 수행합니다.
 * @param {Function} callback 초기화 후 실행할 콜백 함수
 */
async function initPage(callback) {
  try {
    // 사용자 정보 가져오기
    const isLoggedInSuccessfully = await fetchCurrentUser();
    
    // 로그인 체크 및 리디렉션
    if (!isLoggedInSuccessfully) {
      if (!checkLoginAndRedirect()) {
        return;
      }
    }
    
    // 콜백 함수가 있으면 실행
    if (typeof callback === 'function') {
      callback();
    }
  } catch (error) {
    console.error('페이지 초기화 중 오류 발생:', error);
    alert('페이지 초기화 중 오류가 발생했습니다.');
  }
}

// 페이지 로드 시 자동으로 초기화
document.addEventListener('DOMContentLoaded', function() {
  initPage();
}); 