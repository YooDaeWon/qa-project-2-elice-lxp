import allure
import pytest

from framework.e2euiux.pages import (
    ClassroomPage,
    CourseListPage,
    CoursePage,
    ExamStatusPage,
    LoginPage,
    MainPage,
    MyClassesPage,
)


pytestmark = [
    pytest.mark.exam_status_flow,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


@pytest.fixture(scope="module")
def exam_status_e2e_page(e2e_page, educator_credentials):
    """시험 응시 현황 E2E 시작 상태 준비"""
    login_page = LoginPage(e2e_page)
    login_page.open()
    login_page.login(
        educator_credentials["user_id"],
        educator_credentials["password"],
    )
    login_page.verify_redirect()

    main_page = MainPage(e2e_page)
    main_page.open_my_classes()

    my_classes_page = MyClassesPage(e2e_page)
    my_classes_page.verify_loaded()
    my_classes_page.open_classroom()

    classroom_page = ClassroomPage(e2e_page)
    classroom_page.verify_educator_loaded()

    return e2e_page


@allure.label("tc_id", "36")
@allure.label("priority", "P1")
def test_open_course_list(exam_status_e2e_page):
    """학습 과목 목록 페이지 진입"""
    classroom_page = ClassroomPage(exam_status_e2e_page)
    classroom_page.open_learning_subjects()

    course_list_page = CourseListPage(exam_status_e2e_page)
    course_list_page.verify_page_title()


@allure.label("tc_id", "37")
@allure.label("priority", "P1")
def test_open_sandbox_course(exam_status_e2e_page):
    """SANDBOX 과목 페이지 진입"""
    course_list_page = CourseListPage(exam_status_e2e_page)

    if not course_list_page.has_page_title():
        course_page = CoursePage(exam_status_e2e_page)
        course_page.open_course_list()

    course_list_page.verify_loaded()
    course_list_page.open_sandbox()

    course_page = CoursePage(exam_status_e2e_page)
    course_page.verify_loaded()


@allure.label("tc_id", "38")
@allure.label("priority", "P1")
def test_open_test_status(exam_status_e2e_page):
    """e2e-retake 응시 현황 버튼 확인"""
    course_page = CoursePage(exam_status_e2e_page)
    course_page.expand_test_card("e2e-retake")
    course_page.verify_status_button("e2e-retake")


@allure.label("tc_id", "39")
@allure.label("priority", "P1")
def test_open_exam_status(exam_status_e2e_page):
    """SANDBOX 시험 응시 현황 모달 확인"""
    course_page = CoursePage(exam_status_e2e_page)
    course_page.open_status("e2e-retake")

    status_page = ExamStatusPage(exam_status_e2e_page)
    status_page.verify_loaded()


@allure.label("tc_id", "40")
@allure.label("priority", "P1")
def test_verify_student_status(exam_status_e2e_page):
    """qa6_dm01 응시 완료 상태 확인"""
    status_page = ExamStatusPage(exam_status_e2e_page)
    status_page.verify_student_completed("qa6_dm01")
