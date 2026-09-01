import re

from playwright.sync_api import expect


class BoardPostPage:
    """게시물 상세 페이지"""

    URL = re.compile(r"/classrooms/[^/]+/articles/\d+/?$")

    def __init__(self, page):
        self.page = page
        self.comment_input = page.locator('textarea[name="comment"]')
        self.register_button = page.get_by_role(
            "button",
            name="등록",
            exact=True,
        )
        self.board_list_button = page.get_by_role(
            "button",
            name="글 목록",
            exact=True,
        ).first
        self.comment_items = page.locator(
            'main ul > li:has(div[id="comment"])'
        )

    def verify_loaded(self):
        """게시물 상세 페이지 확인"""
        expect(self.page).to_have_url(self.URL)
        expect(self.comment_input).to_be_visible()

    def get_comment_count(self):
        """현재 댓글 개수 확인"""
        return self.comment_items.count()

    def fill_comment(self, comment):
        """댓글 입력"""
        self.comment_input.fill(comment)

    def register_comment(self):
        """댓글 등록"""
        self.register_button.click()

    def register_comment_twice(self):
        """등록 버튼 빠르게 2회 클릭"""
        self.register_button.click(click_count=2)

    def click_board_list(self):
        """글 목록 페이지 열기"""
        self.board_list_button.click()

    def verify_comment_added(self, previous_count, comment):
        """댓글 한 개 추가 및 내용 확인"""
        expect(self.comment_items).to_have_count(previous_count + 1)
        expect(self.comment_items.last).to_contain_text(comment)
