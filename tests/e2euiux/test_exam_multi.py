import allure
import pytest
from playwright.sync_api import expect

from framework.e2euiux.pages import (
    ClassroomPage,
    CourseListPage,
    CoursePage,
    ExamNoticePage,
    ExamPreparePage,
    ExamTimePage,
    LoginPage,
    MainPage,
    MyClassesPage,
)


pytestmark = [
    pytest.mark.exam_multi,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


def _open_exam_notice(page):
    """시험 사전조건 페이지 열기"""
    prepare_page = ExamPreparePage(page)
    prepare_page.verify_loaded()
    prepare_page.agree_and_next()

    time_page = ExamTimePage(page)
    time_page.verify_loaded()
    time_page.go_next()

    notice_page = ExamNoticePage(page)
    notice_page.verify_loaded()


@pytest.fixture(scope="module")
def multi_tab_exam_pages(e2e_page, reset_e2e01, credentials):
    """두 탭의 e2e-01 시험 사전조건 상태 준비"""
    login_page = LoginPage(e2e_page)
    login_page.open()
    login_page.login(
        credentials["user_id"],
        credentials["password"],
    )
    login_page.verify_redirect()

    main_page = MainPage(e2e_page)
    main_page.open_my_classes()

    my_classes_page = MyClassesPage(e2e_page)
    my_classes_page.verify_loaded()
    my_classes_page.open_classroom()

    classroom_page = ClassroomPage(e2e_page)
    classroom_page.verify_loaded()
    classroom_page.open_learning_subjects()

    course_page = CoursePage(e2e_page)
    course_list_page = CourseListPage(e2e_page)
    expect(
        course_list_page.page_title.or_(course_page.lesson_list_tab).first
    ).to_be_visible()

    if course_list_page.has_page_title():
        course_list_page.open_sandbox()

    course_page.verify_loaded()
    course_page.start_test("e2e-01")
    _open_exam_notice(e2e_page)

    second_page = e2e_page.context.new_page()
    second_page.goto(LoginPage.URL)

    second_main_page = MainPage(second_page)
    second_main_page.open_my_classes()

    second_my_classes_page = MyClassesPage(second_page)
    second_my_classes_page.verify_loaded()
    second_my_classes_page.open_classroom()

    second_classroom_page = ClassroomPage(second_page)
    second_classroom_page.verify_loaded()
    second_classroom_page.open_learning_subjects()

    second_course_page = CoursePage(second_page)
    second_course_list_page = CourseListPage(second_page)
    expect(
        second_course_list_page.page_title.or_(
            second_course_page.lesson_list_tab
        ).first
    ).to_be_visible()

    if second_course_list_page.has_page_title():
        second_course_list_page.open_sandbox()

    second_course_page.verify_loaded()
    second_course_page.resume_test("e2e-01")
    _open_exam_notice(second_page)

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
