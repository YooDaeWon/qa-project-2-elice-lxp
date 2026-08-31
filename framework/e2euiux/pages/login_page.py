from playwright.sync_api import expect


class LoginPage:
    """로그인 페이지"""

    URL = "https://dev-qatrack-web.dev.elicer.io/lxp"

    def __init__(self, page):
        self.page = page
        self.login_id = page.locator('input[name="loginId"]')
        self.password = page.locator('input[name="password"]')
        self.login_button = page.get_by_role("button", name="로그인")

    def open(self):
        """로그인 페이지 열기"""
        self.page.goto(self.URL)

    def login(self, user_id, password):
        """아이디와 비밀번호로 로그인"""
        self.login_id.fill(user_id)
        self.password.fill(password)
        self.login_button.click()

    def verify_redirect(self):
        """로그인 후 대상 페이지 전환 확인"""
        expect(self.page).to_have_url(self.URL, timeout=60_000)
