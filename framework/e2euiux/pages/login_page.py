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
        self.invalid_credentials_message = page.get_by_text(
            "이메일 또는 비밀번호가 일치하지 않습니다.",
            exact=True,
        )
        self.organization_name = page.get_by_text(
            "Default Organization 기관 교육",
            exact=True,
        ).first
        self.history_message = page.get_by_text(
            "다시 만나 반갑습니다",
            exact=True,
        )
        self.clear_history_button = page.get_by_role(
            "button",
            name="기록 삭제",
            exact=True,
        )
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

    def _submit_credentials(self, user_id, password):
        """아이디와 비밀번호 제출"""
        self.fill_login_id(user_id)
        self.fill_password(password)
        self.submit_login()

    def _restart_login_from_history(self, user_id, password):
        """로그인 기록 삭제 후 처음부터 로그인"""
        self.clear_history_button.click()
        self._submit_credentials(user_id, password)

    def _register_history_relogin(self, user_id, password):
        """로그인 기록 화면 자동 복구 등록"""
        self.page.add_locator_handler(
            self.history_message,
            lambda: self._restart_login_from_history(user_id, password),
        )

    def open(self):
        """로그인 페이지 열기"""
        self.page.goto(self.URL)

    def fill_login_id(self, user_id):
        """아이디 입력"""
        self.login_id.fill(user_id)

    def fill_password(self, password):
        """비밀번호 입력"""
        self.password.fill(password)

    def submit_login(self):
        """로그인 제출"""
        expect(self.login_button).to_be_enabled()
        self.login_button.click()

    def login(self, user_id, password):
        """아이디와 비밀번호로 로그인"""
        if self._is_history_page():
            self._restart_login_from_history(user_id, password)
        else:
            self._submit_credentials(user_id, password)

        self._register_history_relogin(user_id, password)

    def verify_redirect(self):
        """로그인 후 대상 페이지 전환 확인"""
        expect(self.page).to_have_url(self.URL, timeout=60_000)

    def verify_login_success(self):
        """로그인 후 메인 화면 표시 확인"""
        expect(self.organization_name).to_be_visible()

    def verify_invalid_credentials_message(self):
        """로그인 정보 불일치 메시지 확인"""
        expect(self.invalid_credentials_message).to_be_visible()

    def verify_login_id_required(self):
        """아이디 필수 입력 메시지 확인"""
        validation = self.login_id.evaluate(
            """element => ({
                message: element.validationMessage,
                valueMissing: element.validity.valueMissing,
            })"""
        )
        assert validation["valueMissing"], "아이디 빈 칸 검증이 적용되지 않음"
        assert validation["message"], "아이디 필수 입력 메시지가 표시되지 않음"
        expect(self.login_id).to_be_focused()

    def verify_password_required(self):
        """비밀번호 필수 입력 메시지 확인"""
        validation = self.password.evaluate(
            """element => ({
                message: element.validationMessage,
                valueMissing: element.validity.valueMissing,
            })"""
        )
        assert validation["valueMissing"], "비밀번호 빈 칸 검증이 적용되지 않음"
        assert validation["message"], "비밀번호 필수 입력 메시지가 표시되지 않음"
        expect(self.password).to_be_focused()

    def get_auth_response_summary(self):
        """인증 도메인 응답 요약 반환"""
        if not self.auth_responses:
            return "인증 도메인 응답 없음"
        return "\n".join(self.auth_responses)
