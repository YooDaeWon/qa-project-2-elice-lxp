from playwright.sync_api import expect


class ExamCompletePage:
    """테스트 완료 페이지"""

    def __init__(self, page):
        self.page = page
        self.complete_message = page.get_by_text(
            "테스트가 종료되었습니다.",
            exact=True,
        )
        self.next_button = page.get_by_role(
            "button",
            name="다음",
            exact=True,
        )

    def verify_loaded(self):
        """테스트 완료 페이지 확인"""
        expect(self.complete_message).to_be_visible()

    def open_result(self):
        """테스트 결과 페이지 열기"""
        self.next_button.click()
