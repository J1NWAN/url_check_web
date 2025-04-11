// frontend/common/layout-loader.js
(async () => {
    // 스타일/콘텐츠 로드 전 깜빡임(FOUC) 방지
    document.documentElement.style.visibility = 'hidden';

    // 레이아웃을 가져와 적용하는 함수
    const applyLayout = async () => {
        console.log("[레이아웃 로더] 레이아웃 적용 시작...");
        // HTML 파일(signin/signup) 기준 상대 경로
        const layoutPath = '../common/layout/auth-layout.html';
        console.log(`[레이아웃 로더] 레이아웃 가져오는 중: ${layoutPath}`);
        try {
            // --- 1. 공통 레이아웃 가져오기 ---
            const response = await fetch(layoutPath);
            console.log(`[레이아웃 로더] Fetch 응답 상태: ${response.status}, 성공: ${response.ok}`);

            if (!response.ok) {
                throw new Error(`레이아웃 가져오기 실패: ${response.status} ${response.statusText}`);
            }
            const layoutText = await response.text();
            console.log("[레이아웃 로더] 가져온 레이아웃 텍스트 (앞 300자):", layoutText.substring(0, 300));
            const layoutDoc = new DOMParser().parseFromString(layoutText, 'text/html');

            // --- 2. 현재 페이지에서 콘텐츠 추출 ---
            const pageTitle = document.title || '기본 제목';
            // 현재 body의 모든 내용 가져오기
            const pageContentHTML = document.body.innerHTML;
            // 특정 요소를 찾기 위해 head 복제
            const pageHeadElements = document.head.cloneNode(true);

            // 필요 시 특정 스타일/스크립트 링크 추출 (더 복잡함)
            // 단순화를 위해, 현재는 특정 스타일/스크립트가 body 콘텐츠 내에 링크되어 있다고 가정
            // 또는 필요 시 원본 head의 link/script 태그에 특정 ID/속성 사용

            // --- 3. 레이아웃 플레이스홀더에 콘텐츠 삽입 ---
            const layoutTitleEl = layoutDoc.querySelector('[data-layout-placeholder="page-title"]');
            if (layoutTitleEl) layoutTitleEl.textContent = pageTitle;
            // 문서 제목 직접 설정으로 대체
            else if (layoutDoc.title) layoutDoc.title = pageTitle;

            const placeholderSelector = '[data-layout-placeholder="page-content"]';
            console.log(`[레이아웃 로더] 플레이스홀더 찾는 중: ${placeholderSelector}`);
            const layoutContentEl = layoutDoc.querySelector(placeholderSelector);

            if (layoutContentEl) {
                console.log("[레이아웃 로더] 플레이스홀더 발견!");
                // 원본 body 콘텐츠 삽입
                layoutContentEl.innerHTML = pageContentHTML;
            } else {
                console.warn('가져온 HTML에서 "page-content" 플레이스홀더를 찾지 못했습니다.');
                console.log("[레이아웃 로더] 가져온 레이아웃 문서 구조 (전체):", layoutDoc.documentElement.outerHTML);
            }

            // 페이지별 스타일 플레이스홀더 콘텐츠 삽입 (있을 경우)
            // const pageStylesContainer = pageHeadElements.querySelector('#page-specific-styles-container'); // 예시 ID
            // const layoutStylesPlaceholder = layoutDoc.querySelector('[data-layout-placeholder="page-styles"]');
            // if (pageStylesContainer && layoutStylesPlaceholder) {
            //    layoutStylesPlaceholder.innerHTML = pageStylesContainer.innerHTML;
            // }

            // 페이지별 스크립트 플레이스홀더 콘텐츠 삽입 (있을 경우)
            // const pageScriptsContainer = document.body.querySelector('#page-specific-scripts-container'); // 예시 ID
            // const layoutScriptsPlaceholder = layoutDoc.querySelector('[data-layout-placeholder="page-scripts"]');
            // if (pageScriptsContainer && layoutScriptsPlaceholder) {
            //     layoutScriptsPlaceholder.innerHTML = pageScriptsContainer.innerHTML;
            // }


            // --- 4. 현재 문서 교체 ---
            document.documentElement.innerHTML = layoutDoc.documentElement.innerHTML;
            console.log("[레이아웃 로더] 문서 교체 완료.");

             // --- 5. 원본 페이지 body에 있던 스크립트 재실행 ---
             const injectedContentArea = document.querySelector(placeholderSelector);
             if (injectedContentArea) {
                 console.log("[레이아웃 로더] 삽입된 콘텐츠 내 스크립트 재실행 중...");
                 const scriptsToRun = injectedContentArea.querySelectorAll('script');
                 scriptsToRun.forEach(oldScript => {
                     const newScript = document.createElement('script');
                     // 속성 복사 (src, type 등)
                     Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                     // 인라인 콘텐츠 복사
                     newScript.textContent = oldScript.textContent;
                     // 실행을 위해 body에 추가 (또는 다른 위치)
                     // 원래 위치에서 교체하여 실행 순서 유지
                     oldScript.parentNode.replaceChild(newScript, oldScript);
                     // document.body.appendChild(newScript); // 또는 끝에 추가
                 });
                 console.log(`[레이아웃 로더] 처리된 스크립트 수: ${scriptsToRun.length}`);
             }


        } catch (error) {
            console.error('레이아웃 적용 중 오류:', error);
            // 오류 메시지를 눈에 띄게 표시
            document.documentElement.innerHTML = `
                <head><title>레이아웃 오류</title></head>
                <body style="margin: 20px; font-family: sans-serif;">
                    <h1>레이아웃 오류</h1>
                    <p>페이지 레이아웃을 로드할 수 없습니다.</p>
                    <pre style="color: red; background: #fdd; padding: 10px; border: 1px solid red;">${error.stack || error}</pre>
                </body>`;
        } finally {
             // 오류 발생 시에도 페이지가 보이도록 보장 (파싱 오류 제외)
             requestAnimationFrame(() => {
                  document.documentElement.style.visibility = 'visible';
             });
             console.log("[레이아웃 로더] 레이아웃 처리 완료.");
        }
    };

    // 레이아웃 적용 로직 실행
    // 초기 페이지 요소가 파싱되도록 DOMContentLoaded 사용
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyLayout);
    } else {
        // 이미 로드됨
        applyLayout();
    }

})(); 