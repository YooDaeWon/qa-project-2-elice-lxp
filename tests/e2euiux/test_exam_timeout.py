import allure
import pytest

from framework.e2euiux.pages import (
    ClassroomPage,
    CourseListPage,
    CoursePage,
    ExamNoticePage,
    ExamPage,
    ExamPreparePage,
    ExamTimePage,
    LoginPage,
    MainPage,
    MyClassesPage,
)


pytestmark = [
    pytest.mark.exam_timeout,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


def _open_timeout_exam_page(page, credentials):
    """timeout 시험 답안 입력 페이지 열기"""
    login_page = LoginPage(page)
    login_page.open()
    login_page.login(
        credentials["user_id"],
        credentials["password"],
    )
    login_page.verify_redirect()

    main_page = MainPage(page)
    main_page.open_my_classes()

    my_classes_page = MyClassesPage(page)
    my_classes_page.verify_loaded()
    my_classes_page.open_classroom()

    classroom_page = ClassroomPage(page)
    classroom_page.verify_loaded()
    classroom_page.open_learning_subjects()

    course_list_page = CourseListPage(page)
    course_page = CoursePage(page)
    course_list_or_course = course_list_page.page_title.or_(
        course_page.lesson_list_tab
    ).first
    course_list_or_course.wait_for(state="visible")

    if course_list_page.is_course_list_visible():
        course_list_page.open_sandbox()

    course_page.verify_loaded()
    course_page.start_test("timeout")

    prepare_page = ExamPreparePage(page)
    prepare_page.verify_timeout_loaded()
    prepare_page.agree_and_next()

    time_page = ExamTimePage(page)
    time_page.verify_loaded()
    time_page.go_next()

    notice_page = ExamNoticePage(page)
    notice_page.verify_loaded()
    notice_page.start_test()

    exam_page = ExamPage(page)
    exam_page.verify_loaded()
    return exam_page


@allure.label("tc_id", "48")
@allure.label("priority", "P1")
def test_verify_timeout_modal(
    e2e_page,
    credentials,
    reset_timeout,
):
    """제한 시간 종료 모달 확인"""
    e2e_page.clock.install()
    exam_page = _open_timeout_exam_page(e2e_page, credentials)
    e2e_page.clock.fast_forward("04:58")
    exam_page.verify_timeout_modal(timeout=10_000)
