import re

from playwright.sync_api import expect


class ExamPreparePage:
    """테스트 준비하기 페이지"""

    URL = re.compile(r"/test/onboard/info/?$")

    def __init__(self, page):
        self.page = page
        self.agreement_checkbox = page.locator('input[type="checkbox"]')
        self.next_button = page.get_by_role(
            "button",
            name="다음",
            exact=True,
        )

    def verify_loaded(self):
        """테스트 준비하기 페이지 확인"""
        expect(self.page).to_have_url(self.URL)

    def agree_and_next(self):
        """유의 사항 동의 후 다음 페이지 열기"""
        self.agreement_checkbox.check()
        self.next_button.click()
