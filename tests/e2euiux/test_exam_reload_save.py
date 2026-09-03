import secrets

import allure
import pytest
from playwright.sync_api import expect

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
    pytest.mark.exam_reload_save,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


@pytest.fixture(scope="module")
def auto_save_answer():
    """자동 저장 검증용 8자리 랜덤 문자열"""
    return secrets.token_hex(4)


def _open_exam_page(page):
    """시험 응시 페이지 열기"""
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


@allure.label("tc_id", "42")
@allure.label("priority", "P2")
def test_verify_answer_auto_save(
    e2e_page,
    credentials,
    reset_e2e01,
    auto_save_answer,
):
    """새로고침 후 답안 자동 저장 확인"""
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

    course_list_page = CourseListPage(e2e_page)
    course_page = CoursePage(e2e_page)
    course_list_or_course = course_list_page.page_title.or_(
        course_page.lesson_list_tab
    ).first
    expect(course_list_or_course).to_be_visible()

    if course_list_page.is_course_list_visible():
        course_list_page.open_sandbox()

    course_page.verify_loaded()
    course_page.start_test("e2e-01")
    _open_exam_page(e2e_page)

    exam_page = ExamPage(e2e_page)
    exam_page.enter_answer(auto_save_answer)
    e2e_page.reload()
    exam_page.verify_loaded()
    exam_page.verify_answer_saved(auto_save_answer)
