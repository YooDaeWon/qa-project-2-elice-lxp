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
    pytest.mark.exam_offline,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


def _open_exam_page(page, credentials):
    """답안 입력 페이지까지 열기"""
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

    if course_list_page.has_page_title():
        course_list_page.open_sandbox()
        course_page.verify_loaded()

    course_page.start_test("e2e-01")

    prepare_page = ExamPreparePage(page)
    prepare_page.verify_loaded()
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


@allure.label("tc_id", "47")
@allure.label("priority", "P2")
def test_submit_exam_offline(
    e2e_page,
    credentials,
    reset_e2e01,
):
    """네트워크 차단 후 제출 오류 확인"""
    exam_page = _open_exam_page(e2e_page, credentials)
    exam_page.enter_answer("offline")
    exam_page.verify_submit_enabled()

    e2e_page.context.set_offline(True)
    try:
        exam_page.submit_answer()
        exam_page.verify_question_load_error()
    finally:
        e2e_page.context.set_offline(False)
