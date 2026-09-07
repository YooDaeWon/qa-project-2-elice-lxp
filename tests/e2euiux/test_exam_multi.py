import allure
import pytest

from framework.e2euiux.flows import (
    login_to_main,
    open_classroom_from_main,
    open_exam_notice,
    open_sandbox_for_setup,
)
from framework.e2euiux.pages import (
    ExamNoticePage,
    LoginPage,
)


pytestmark = [
    pytest.mark.exam_multi,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


@pytest.fixture(scope="module")
def multi_tab_exam_pages(e2e_page, reset_e2e01, credentials):
    """두 탭의 e2e-01 시험 사전조건 상태 준비"""
    login_to_main(e2e_page, credentials)

    classroom_page = open_classroom_from_main(e2e_page)
    classroom_page.verify_loaded()
    classroom_page.open_learning_subjects()

    course_page = open_sandbox_for_setup(e2e_page)
    course_page.start_test("e2e-01")
    open_exam_notice(e2e_page)

    second_page = e2e_page.context.new_page()
    second_page.goto(LoginPage.URL)

    second_classroom_page = open_classroom_from_main(second_page)
    second_classroom_page.verify_loaded()
    second_classroom_page.open_learning_subjects()

    second_course_page = open_sandbox_for_setup(second_page)
    second_course_page.resume_test("e2e-01")
    open_exam_notice(second_page)

    yield {
        "first_page": e2e_page,
        "second_page": second_page,
    }

    second_page.close()


@allure.label("tc_id", "41")
@allure.label("priority", "P2")
def test_start_exam_in_two_tabs(multi_tab_exam_pages):
    """두 탭에서 테스트 시작 및 오류 확인"""
    first_page = multi_tab_exam_pages["first_page"]
    second_page = multi_tab_exam_pages["second_page"]

    ExamNoticePage(first_page).start_test(no_wait_after=True)
    first_page.wait_for_timeout(500)
    notice_page = ExamNoticePage(second_page)
    with second_page.expect_response("**/lecture/test/start/"):
        notice_page.start_test(no_wait_after=True)
    notice_page.verify_start_error()
