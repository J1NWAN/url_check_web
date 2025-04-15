# Firebase 서비스 계정 키 설정 안내

이 폴더는 Firebase Firestore 연결을 위한 서비스 계정 키 파일을 저장하는 곳입니다.

## 서비스 계정 키 생성 방법

1. [Firebase 콘솔](https://console.firebase.google.com/)에 로그인합니다.
2. 프로젝트를 선택하거나 새로 생성합니다.
3. 좌측 메뉴에서 "⚙️ 프로젝트 설정"을 클릭합니다.
4. "서비스 계정" 탭을 선택합니다.
5. "새 비공개 키 생성" 버튼을 클릭합니다.
6. 다운로드된 JSON 파일을 이 폴더에 `serviceAccountKey.json` 이름으로 저장합니다.

## 주의사항

- 서비스 계정 키 파일은 절대 버전 관리 시스템(Git 등)에 포함시키지 마세요.
- `.gitignore` 파일에 `serviceAccountKey.json`을 추가하여 실수로 커밋되지 않도록 하세요.
- 보안을 위해 프로덕션 환경에서는 환경 변수를 사용하는 것이 권장됩니다.

## 환경 변수 사용 방법 (선택 사항)

코드에서 환경 변수로 서비스 계정 키 경로를 지정하려면:

```bash
# Linux/macOS
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/serviceAccountKey.json"

# Windows
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\serviceAccountKey.json
```

그리고 `backend/config/database.py` 파일에서 주석 처리된 환경 변수 사용 코드를 활성화하세요. 