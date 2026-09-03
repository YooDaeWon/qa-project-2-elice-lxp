from playwright.sync_api import expect


class NotFoundPage:
    """존재하지 않는 URL의 오류 페이지"""

    def __init__(self, page):
        self.page = page
        self.not_found_message = page.get_by_text(
            "페이지를 찾을 수 없습니다.",
            exact=True,
        )
        self.go_back_button = page.get_by_role(
            "button",
            name="이전 페이지로 가기",
            exact=True,
        )

    def open_invalid_url(self):
        """현재 LXP URL 뒤에 잘못된 경로 추가"""
        self.page.goto(f"{self.page.url}test")

    def verify_loaded(self):
        """페이지를 찾을 수 없음 화면 확인"""
        expect(self.not_found_message).to_be_visible()
        expect(self.go_back_button).to_be_visible()
