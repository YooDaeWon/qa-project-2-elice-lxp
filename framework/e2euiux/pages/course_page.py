import re

from playwright.sync_api import expect


class CoursePage:
    """SANDBOX 과목 페이지"""

    def __init__(self, page):
        self.page = page
        self.course_list_button = page.get_by_role(
            "button",
            name="과목 목록",
            exact=True,
        )
        self.lesson_list_tab = page.get_by_role(
            "tab",
            name="수업 목록",
            exact=True,
        )
        self.learning_status_tab = page.get_by_role(
            "tab",
            name="학습 현황",
            exact=True,
        )

    def verify_loaded(self):
        """시험 과목 페이지 확인"""
        expect(self.lesson_list_tab).to_be_visible()
        expect(self.learning_status_tab).to_be_visible()

    def open_course_list(self):
        """학습 과목 목록 페이지 열기"""
        self.course_list_button.click()

    def start_test(self, test_name):
        """지정한 테스트 시작하기"""
        test_card = self.page.get_by_role(
            "button",
            name=re.compile(re.escape(test_name)),
        )
        test_card.get_by_role(
            "button",
            name="테스트 시작하기",
            exact=True,
        ).click()
