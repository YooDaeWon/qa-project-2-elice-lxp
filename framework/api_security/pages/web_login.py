"""api_security 전용 최소 브라우저 로그인 헬퍼.

대부분의 api_security 테스트는 requests 기반 토큰/세션으로 호출하지만,
ID-38(저장된 XSS의 브라우저 실행 여부)처럼 실제 렌더링 확인이 필요한
소수 케이스만 Playwright 브라우저 로그인이 필요하다.

팀 e2e 테스트가 쓰는 framework/e2euiux/pages/login_page.py를 그대로 가져다
쓰지 않는 이유: 각 담당 영역(framework/api, framework/api_security,
framework/e2euiux, framework/loadtest)은 서로 독립적으로 유지되도록 구성되어
있고, 다른 팀 브랜치의 변경이 여기로 새어 들어와 우리 테스트를 깨뜨리는 것을
막기 위해 이 파일이 필요로 하는 최소 기능만 별도로 둔다.
"""

from playwright.sync_api import expect


def login_via_ui(page, user_id: str, password: str, web_base_url: str) -> None:
    """로그인 폼을 채우고 제출한다.

    버튼이 DOM에 나타난 뒤에도 잠깐 비활성 상태로 남아있을 수 있어
    클릭 전에 활성화를 명시적으로 기다린다.
    """
    page.goto(f"{web_base_url}/lxp")
    page.locator('input[name="loginId"]').fill(user_id)
    page.locator('input[name="password"]').fill(password)

    login_button = page.get_by_role("button", name="로그인")
    expect(login_button).to_be_enabled()
    login_button.click()

    page.wait_for_url(f"{web_base_url}/lxp", timeout=60_000)
