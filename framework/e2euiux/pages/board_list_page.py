import re

from playwright.sync_api import expect


class BoardListPage:
    """게시판 목록 페이지"""

    URL = re.compile(r"/classrooms/[^/]+/articles(?:\?page=\d+)?/?$")

    def __init__(self, page):
        self.page = page
        self.page_title = page.get_by_role(
            "heading",
            name="게시판",
            exact=True,
        )
        self.write_button = page.get_by_role(
            "button",
            name="글쓰기",
            exact=True,
        )

    def verify_loaded(self):
        """게시판 목록 페이지 확인"""
        expect(self.page).to_have_url(self.URL)
        expect(self.page_title).to_be_visible()
        self.page.wait_for_timeout(500)

    def open_write(self):
        """글쓰기 페이지 열기"""
        self.write_button.click()
