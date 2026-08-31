from playwright.sync_api import expect


class ExamResultPage:
    """테스트 결과 페이지"""

    def __init__(self, page):
        self.page = page
        self.test_complete_message = page.get_by_text(
            "테스트 응시 완료",
            exact=True,
        )

    def verify_loaded(self):
        """테스트 결과 페이지 전환 확인"""
        expect(self.test_complete_message).to_be_visible()
