from playwright.sync_api import expect


class ExamTimePage:
    """PC 시간 설정 페이지"""

    def __init__(self, page):
        self.page = page
        self.next_button = page.get_by_role(
            "button",
            name="다음",
            exact=True,
        )
        self.server_time_text = page.get_by_text(
            "서버 시간",
            exact=True,
        )

    def verify_loaded(self):
        """PC 시간 설정 페이지 확인"""
        expect(self.server_time_text).to_be_visible()

    def go_next(self):
        """유의 사항 확인 페이지 열기"""
        self.next_button.click()
