import allure
import pytest

from framework.e2euiux.flows import (
    login_to_main,
    open_classroom_from_main,
)
from framework.e2euiux.pages import (
    ClassroomPage,
    CoursePage,
    SchedulePage,
)


pytestmark = [
    pytest.mark.schedule_flow,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


@pytest.fixture(scope="module")
def schedule_e2e_page(e2e_page, credentials):
    """수업 일정 E2E 시작 상태 준비"""
    login_to_main(e2e_page, credentials)

    classroom_page = open_classroom_from_main(e2e_page)
    classroom_page.verify_loaded()

    return e2e_page


@allure.label("tc_id", "21")
@allure.label("priority", "P1")
def test_open_schedule(schedule_e2e_page):
    """수업 일정 페이지 진입"""
    classroom_page = ClassroomPage(schedule_e2e_page)
    classroom_page.open_schedule()

    schedule_page = SchedulePage(schedule_e2e_page)
    schedule_page.verify_loaded()


@allure.label("tc_id", "22")
@allure.label("priority", "P1")
def test_open_test_schedule_shows_side_panel(schedule_e2e_page):
    """test 일정 사이드 패널 확인"""
    schedule_page = SchedulePage(schedule_e2e_page)
    schedule_page.open_test_schedule()
    schedule_page.verify_test_panel()


@allure.label("tc_id", "23")
@allure.label("priority", "P1")
def test_click_linked_class_button(schedule_e2e_page):
    """연결된 클래스 버튼 클릭 후 학습 과목 페이지 확인"""
    schedule_page = SchedulePage(schedule_e2e_page)
    schedule_page.click_linked_class_button()

    course_page = CoursePage(schedule_e2e_page)
    course_page.verify_loaded()
