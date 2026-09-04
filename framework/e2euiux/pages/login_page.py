from urllib.parse import urlparse

from playwright.sync_api import expect


class LoginPage:
    """로그인 페이지"""

    URL = "https://dev-qatrack-web.dev.elicer.io/lxp"
    HISTORY_PATH = "/accounts/signin/history"

    def __init__(self, page):
        self.page = page
        self.login_id = page.locator('input[name="loginId"]')
        self.password = page.locator('input[name="password"]')
        self.login_button = page.get_by_role("button", name="로그인")
        self.organization_name = page.get_by_text(
            "Default Organization 기관 교육",
            exact=True,
        ).first
        self.auth_responses = []
        self.page.on("response", self._record_auth_response)

    def _record_auth_response(self, response):
        """인증 도메인 응답 기록"""
        parsed_url = urlparse(response.url)
        if "accounts" not in parsed_url.netloc.lower() and not (
            parsed_url.path.startswith("/accounts/")
        ):
            return

        result = "OK" if response.status < 400 else "ERROR"
        self.auth_responses.append(
            f"{result} {response.request.method} "
            f"{response.status} {parsed_url.path}"
        )

    def _is_history_page(self):
        """로그인 기록 화면 여부 확인"""
        return urlparse(self.page.url).path.rstrip("/") == self.HISTORY_PATH

    def open(self):
        """로그인 페이지 열기"""
        self.page.goto(self.URL)

    def login(self, user_id, password):
        """아이디와 비밀번호로 로그인"""
        if not self._is_history_page():
            self.login_id.fill(user_id)

        self.password.fill(password)
        expect(self.login_button).to_be_enabled()
        self.login_button.click()

    def verify_redirect(self):
        """로그인 후 대상 페이지 전환 확인"""
        expect(self.page).to_have_url(self.URL, timeout=60_000)

    def verify_login_success(self):
        """로그인 후 메인 화면 표시 확인"""
        expect(self.organization_name).to_be_visible()

    def get_auth_response_summary(self):
        """인증 도메인 응답 요약 반환"""
        if not self.auth_responses:
            return "인증 도메인 응답 없음"
        return "\n".join(self.auth_responses)
