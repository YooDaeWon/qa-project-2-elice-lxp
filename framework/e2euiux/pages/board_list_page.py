import re

from playwright.sync_api import expect


class BoardListPage:
    """게시판 목록 페이지"""

    URL = re.compile(r"/classrooms/[^/]+/articles\?page=1/?$")

    def __init__(self, page):
        self.page = page
        self.write_button = page.get_by_role(
            "button",
            name="글쓰기",
            exact=True,
        )

    def verify_loaded(self):
        """게시판 목록 페이지 확인"""
        expect(self.page).to_have_url(self.URL)
        expect(self.write_button).to_be_visible()
        expect(self.write_button).to_be_enabled()
        self.page.wait_for_timeout(500)

    def open_write(self):
        """글쓰기 페이지 열기"""
        self.write_button.click()

    def _post_items(self, title):
        """게시판에서 제목과 일치하는 게시물 찾기"""
        return self.page.locator("main").get_by_text(
            title,
            exact=True,
        ).locator(":scope:visible")

    def get_post_count(self, title):
        """제목과 일치하는 게시글 개수 확인"""
        return self._post_items(title).count()

    def verify_single_post_created(self, title, previous_count):
        """중복 요청 후 게시글 한 개 생성 확인"""
        post_items = self._post_items(title)
        new_post = post_items.nth(previous_count)
        new_post.wait_for(state="visible", timeout=30_000)

        actual_count = post_items.count()
        assert actual_count == previous_count + 1, (
            f"게시글 중복 생성됨: 기대 {previous_count + 1}개, "
            f"실제 {actual_count}개"
        )
