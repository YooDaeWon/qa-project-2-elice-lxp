import re

from playwright.sync_api import expect


class MyClassesPage:
    """내 클래스 페이지"""

    URL = re.compile(r"/my-classes/classrooms/?$")

    def __init__(self, page):
        self.page = page
        self.class_card = page.get_by_role(
            "button",
            name=re.compile(r"\[QA6_4팀\]\s+최종프로젝트"),
        )

    def verify_loaded(self):
        """내 클래스 페이지 확인"""
        expect(self.page).to_have_url(self.URL)

    def open_classroom(self):
        """QA6_4팀 클래스 페이지 열기"""
        self.class_card.click()
