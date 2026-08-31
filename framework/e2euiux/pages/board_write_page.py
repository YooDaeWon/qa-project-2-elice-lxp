import re

from playwright.sync_api import expect


class BoardWritePage:
    """게시물 글쓰기 페이지"""

    URL = re.compile(r"/classrooms/[^/]+/articles/write/?$")

    def __init__(self, page):
        self.page = page
        self.title_input = page.locator('input[name="title"]')
        self.content_editor = page.locator(
            '[data-lexical-editor="true"][contenteditable="true"]'
        )
        self.save_button = page.get_by_role(
            "button",
            name="저장",
            exact=True,
        )

    def verify_loaded(self):
        """게시물 글쓰기 페이지 확인"""
        expect(self.page).to_have_url(self.URL)
        expect(self.save_button).to_be_visible()

    def fill_title(self, title):
        """게시물 제목 입력"""
        self.title_input.fill(title)

    def fill_content(self, content): 
        """게시물 내용 앞부분(나눠입력함)"""
        self.content_editor.click()
        self.content_editor.type(content)

    def append_content(self, content):
        """게시물 내용 이어서 입력, 게시물 내용을 fill(test body)로
        한번에 들어가면 [저장] 버튼이 활성화 안 됨 이슈
        따라서 두 번에 나눠 입력하는 방법을 선택함"""
        self.content_editor.type(content)

    def verify_save_enabled(self):
        """저장 버튼 활성화 확인""" 
        expect(self.save_button).to_be_enabled()

    def save(self):
        """게시물 저장"""
        self.save_button.click()
