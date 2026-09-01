import re

from playwright.sync_api import expect


class ClassroomPage:
    """클래스 대시보드 페이지"""

    URL = re.compile(r"/classrooms/[^/]+/?$")

    def __init__(self, page):
        self.page = page
        self.learning_subjects_link = page.get_by_role(
            "link",
            name="학습 과목",
            exact=True,
        )
        self.board_link = page.get_by_role(
            "link",
            name="게시판",
            exact=True,
        )
        self.schedule_link = page.get_by_role(
            "link",
            name="수업 일정",
            exact=True,
        )
        self.educator_welcome_message = page.get_by_text(
            re.compile(r"안녕하세요, .+님"),
        )

    def verify_loaded(self):
        """클래스 대시보드 페이지 확인"""
        expect(self.page).to_have_url(self.URL)

    def verify_educator_loaded(self):
        """교육자 클래스 대시보드 페이지 확인"""
        expect(self.educator_welcome_message).to_be_visible()

    def open_learning_subjects(self):
        """학습 과목 페이지 열기"""
        self.learning_subjects_link.click()

    def open_board(self):
        """게시판 페이지 열기"""
        self.board_link.click()

    def open_schedule(self):
        """수업 일정 페이지 열기"""
        self.schedule_link.click()
