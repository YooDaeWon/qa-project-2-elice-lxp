import re

from playwright.sync_api import expect


class SchedulePage:
    """수업 일정 페이지"""

    URL = re.compile(r"/classrooms/[^/]+/schedules/?$")

    def __init__(self, page):
        self.page = page
        self.today_button = page.get_by_role(
            "button",
            name="오늘",
            exact=True,
        )
        self.test_schedule = page.get_by_text(
            "test",
            exact=True,
        )
        self.linked_class_button = page.locator(
            '[role="button"]:has([data-testid="arrow-rightIcon"])',
        )

    def verify_loaded(self):
        """수업 일정 페이지 확인"""
        expect(self.page).to_have_url(self.URL)
        expect(self.today_button).to_be_visible()

    def open_test_schedule(self):
        """test 일정 열기"""
        self.test_schedule.click()

    def verify_test_panel(self):
        """test 수업 사이드 패널 확인"""
        expect(self.linked_class_button).to_be_visible()

    def click_linked_class_button(self):
        """Click linked class button"""
        self.linked_class_button.click()
