from playwright.sync_api import expect


class ExamNoticePage:
    """유의 사항 확인 페이지"""

    def __init__(self, page):
        self.page = page
        self.start_button = page.get_by_role(
            "button",
            name="테스트 시작",
            exact=True,
        )
        self.ready_message = page.get_by_text(
            "모든 응시 준비가 완료되었습니다.",
            exact=True,
        )
        self.start_error_message = page.get_by_text(
            "다시 시도해주세요",
            exact=False,
        )

    def verify_loaded(self):
        """유의 사항 확인 페이지 확인"""
        expect(self.ready_message).to_be_visible()

    def start_test(self, no_wait_after=False):
        """테스트 페이지 열기"""
        self.start_button.click(no_wait_after=no_wait_after)

    def verify_start_error(self):
        """테스트 시작 오류 문구 확인"""
        expect(self.start_error_message).to_be_visible()
