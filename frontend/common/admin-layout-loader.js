// frontend/common/admin-layout-loader.js
(async () => {
    // 스타일/콘텐츠 로드 전 깜빡임(FOUC) 방지
    document.documentElement.style.visibility = 'hidden';

    // 레이아웃을 가져와 적용하는 함수
    const applyLayout = async () => {
        try {
            // --- 1. 관리자 레이아웃 가져오기 ---
            // /admin/ 디렉토리 내 HTML 파일 기준 상대 경로
            const layoutPath = '../common/layout/admin-layout.html';
            const response = await fetch(layoutPath);
            if (!response.ok) {
                throw new Error(`관리자 레이아웃 가져오기 실패: ${response.status} ${response.statusText} 경로: ${layoutPath}`);
            }
            const layoutText = await response.text();
            const layoutDoc = new DOMParser().parseFromString(layoutText, 'text/html');

            // --- 2. 현재 페이지에서 콘텐츠 추출 ---
            const pageTitle = document.title || '관리자 페이지';
            const pageContentHTML = document.body.innerHTML;
            const pageHeadElements = document.head.cloneNode(true);

            // --- 3. 레이아웃 플레이스홀더에 콘텐츠 삽입 ---
            // 제목
            const layoutTitleEl = layoutDoc.querySelector('[data-layout-placeholder="page-title"]');
            if (layoutTitleEl) layoutTitleEl.textContent = pageTitle;
            else if (layoutDoc.title) layoutDoc.title = pageTitle;

            // Breadcrumb 제목 (메인 제목 기반 업데이트)
            const breadcrumbTitleEl = layoutDoc.querySelector('[data-layout-placeholder="breadcrumb-page-title"]');
            if (breadcrumbTitleEl) {
                // "페이지 제목 - 사이트 이름" 형식 가정
                const titleParts = pageTitle.split(' - ');
                breadcrumbTitleEl.textContent = titleParts[0] || '페이지';
            }

            // 페이지 콘텐츠
            const layoutContentEl = layoutDoc.querySelector('[data-layout-placeholder="page-content"]');
            if (layoutContentEl) {
                layoutContentEl.innerHTML = pageContentHTML;
            } else {
                console.warn('관리자 레이아웃 "page-content" 플레이스홀더를 찾지 못했습니다.');
            }

            // 페이지별 스타일 삽입 (예시 - 페이지 head에 특정 요소 필요)
            // const pageStylesContainer = pageHeadElements.querySelector('#page-specific-styles');
            // const layoutStylesPlaceholder = layoutDoc.querySelector('[data-layout-placeholder="page-styles"]');
            // if (pageStylesContainer && layoutStylesPlaceholder) {
            //     layoutStylesPlaceholder.innerHTML = pageStylesContainer.innerHTML;
            // }

            // 페이지별 스크립트 삽입 (예시 - 페이지 body에 특정 요소 필요)
            // const pageScriptsContainer = document.body.querySelector('#page-specific-scripts');
            // const layoutScriptsPlaceholder = layoutDoc.querySelector('[data-layout-placeholder="page-scripts"]');
            // if (pageScriptsContainer && layoutScriptsPlaceholder) {
            //     layoutScriptsPlaceholder.innerHTML = pageScriptsContainer.innerHTML;
            // }

            // --- 4. 현재 문서 교체 ---
            document.documentElement.innerHTML = layoutDoc.documentElement.innerHTML;

            // --- 5. 원본 페이지 body에 있던 스크립트 재실행 ---
            const injectedContentArea = document.querySelector('[data-layout-placeholder="page-content"]');
            if (injectedContentArea) {
                const scriptsToRun = injectedContentArea.querySelectorAll('script');
                scriptsToRun.forEach(oldScript => {
                    const newScript = document.createElement('script');
                    Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                    newScript.textContent = oldScript.textContent;
                    // 다른 요소와의 실행 순서를 유지하기 위해 원래 위치에서 교체
                    oldScript.parentNode.replaceChild(newScript, oldScript);
                });
            }

             // --- 6. 필요 시 레이아웃별 스크립트 재실행 ---
             // 예시: 네비게이션 링크 활성화 (admin-layout.html 자체로 이동됨)
             /*
             const layoutScripts = layoutDoc.querySelectorAll('script[data-layout-script]');
             layoutScripts.forEach(script => {
                 const newScript = document.createElement('script');
                 newScript.textContent = script.textContent;
                 document.body.appendChild(newScript).parentNode.removeChild(newScript);
             });
             */

        } catch (error) {
            console.error('관리자 레이아웃 적용 중 오류:', error);
            document.documentElement.innerHTML = `
                <head><title>레이아웃 오류</title></head>
                <body style="margin: 20px; font-family: sans-serif;">
                    <h1>레이아웃 오류</h1>
                    <p>관리자 페이지 레이아웃을 로드할 수 없습니다.</p>
                    <pre style="color: red; background: #fdd; padding: 10px; border: 1px solid red;">${error.stack || error}</pre>
                </body>`;
        } finally {
            requestAnimationFrame(() => {
                document.documentElement.style.visibility = 'visible';
            });
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyLayout);
    } else {
        applyLayout();
    }

})(); 