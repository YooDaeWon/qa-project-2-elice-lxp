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
        self.class_home_link = page.get_by_role(
            "link",
            name="클래스 홈",
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

    def open_class_home(self):
        """클래스 홈 페이지 열기"""
        self.class_home_link.click()

    def _test_card(self, test_name):
        """시험 이름으로 테스트 카드 찾기"""
        return self.page.get_by_role(
            "button",
            name=re.compile(
                rf"^\d+\s+{re.escape(test_name)}(?:\s|$)"
            ),
        )

    def _test_action_button(self, test_name, button_name):
        """테스트 카드 또는 상세 영역에서 버튼 찾기"""
        test_card = self._test_card(test_name)
        test_region = test_card.locator("xpath=..").get_by_role("region")

        card_button = test_card.get_by_role(
            "button",
            name=button_name,
            exact=True,
        )
        region_button = test_region.get_by_role(
            "button",
            name=button_name,
            exact=True,
        )

        return card_button.or_(region_button).first

    def _click_test_action(self, test_name, button_name):
        """지정한 시험의 동작 버튼 표시를 확인한 뒤 클릭"""
        button = self._test_action_button(test_name, button_name)
        expect(button).to_be_visible()
        button.click()

    def start_test(self, test_name):
        """지정한 테스트 시작하기"""
        self._click_test_action(test_name, "테스트 시작하기")

    def resume_test(self, test_name):
        """진행 중인 테스트 이어하기"""
        self._click_test_action(test_name, "테스트 이어하기")

    def retake_test(self, test_name):
        """지정한 테스트 재응시하기"""
        self._click_test_action(test_name, "테스트 재응시")

    def verify_retake_available(self, test_name):
        """재응시 후 테스트 시작 버튼 확인"""
        start_button = self._test_action_button(
            test_name,
            "테스트 시작하기",
        )
        expect(start_button).to_be_visible()

    def expand_test_card(self, test_name):
        """시험 카드 상세 내용 열기"""
        test_card = self._test_card(test_name)
        if test_card.get_attribute("aria-expanded") != "true":
            test_card.click()

    def verify_status_button(self, test_name):
        """시험 카드의 응시 현황 버튼 확인"""
        status_button = self._test_action_button(
            test_name,
            "응시 현황",
        )
        expect(status_button).to_be_visible()

    def open_status(self, test_name):
        """시험 응시 현황 열기"""
        status_button = self._test_action_button(
            test_name,
            "응시 현황",
        )
        status_button.click()
