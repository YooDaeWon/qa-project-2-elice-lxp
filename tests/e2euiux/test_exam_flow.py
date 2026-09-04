import allure
import pytest

from framework.e2euiux.pages import (
    ClassroomPage,
    CourseListPage,
    CoursePage,
    ExamCompletePage,
    ExamNoticePage,
    ExamPage,
    ExamPreparePage,
    ExamResultPage,
    ExamTimePage,
    LoginPage,
    MainPage,
    MyClassesPage,
)


pytestmark = [
    pytest.mark.exam_flow,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


@allure.label("tc_id", "01")
@allure.label("priority", "P1")
def test_login(
    e2e_page,
    credentials,
    reset_exam,
):
    """로그인 후 메인 페이지 진입"""
    login_page = LoginPage(e2e_page)
    login_page.open()
    login_page.login(credentials["user_id"], credentials["password"])
    login_page.verify_redirect()


@allure.label("tc_id", "02")
@allure.label("priority", "P1")
def test_open_my_classes(e2e_page):
    """내 클래스 페이지 진입"""
    main_page = MainPage(e2e_page)
    main_page.open_my_classes()

    my_classes_page = MyClassesPage(e2e_page)
    my_classes_page.verify_loaded()


@allure.label("tc_id", "03")
@allure.label("priority", "P1")
def test_open_classroom(e2e_page):
    """클래스 페이지 진입"""
    my_classes_page = MyClassesPage(e2e_page)
    my_classes_page.open_classroom()

    classroom_page = ClassroomPage(e2e_page)
    classroom_page.verify_loaded()


@allure.label("tc_id", "04")
@allure.label("priority", "P1")
def test_open_course_list(e2e_page):
    """학습 과목 목록 페이지 진입
    *** FAIL 케이스입니다. [학습 과목] 버튼 클릭 시,
    학습 과목 목록 페이지와 SANDBOX 과목 페이지로 랜덤하게 전환됨"""
    classroom_page = ClassroomPage(e2e_page)
    classroom_page.open_learning_subjects()

    course_list_page = CourseListPage(e2e_page)
    course_list_page.verify_page_title()


@allure.label("tc_id", "05")
@allure.label("priority", "P1")
def test_open_sandbox_course(e2e_page):
    """SANDBOX 과목 페이지 진입"""
    course_list_page = CourseListPage(e2e_page)

    if not course_list_page.is_course_list_visible():
        course_page = CoursePage(e2e_page)
        course_page.open_course_list()

    course_list_page.verify_loaded()
    course_list_page.open_sandbox()

    course_page = CoursePage(e2e_page)
    course_page.verify_loaded()


@allure.label("tc_id", "06")
@allure.label("priority", "P1")
def test_open_exam_prepare(e2e_page):
    """테스트 준비하기 페이지 진입"""
    course_page = CoursePage(e2e_page)
    course_page.start_test("e2e-01")

    prepare_page = ExamPreparePage(e2e_page)
    prepare_page.verify_loaded()


@allure.label("tc_id", "07")
@allure.label("priority", "P1")
def test_open_exam_time(e2e_page):
    """PC 시간 설정 페이지 진입"""
    prepare_page = ExamPreparePage(e2e_page)
    prepare_page.agree_and_next()

    time_page = ExamTimePage(e2e_page)
    time_page.verify_loaded()


@allure.label("tc_id", "08")
@allure.label("priority", "P1")
def test_open_exam_notice(e2e_page):
    """유의 사항 확인 페이지 진입"""
    time_page = ExamTimePage(e2e_page)
    time_page.go_next()

    notice_page = ExamNoticePage(e2e_page)
    notice_page.verify_loaded()


@allure.label("tc_id", "09")
@allure.label("priority", "P1")
def test_open_exam(e2e_page):
    """테스트 페이지 진입"""
    notice_page = ExamNoticePage(e2e_page)
    notice_page.start_test()

    exam_page = ExamPage(e2e_page)
    exam_page.verify_loaded()


@allure.label("tc_id", "10")
@allure.label("priority", "P1")
def test_verify_submit_enabled(e2e_page):
    """답안 입력 후 제출 버튼 활성화 확인"""
    exam_page = ExamPage(e2e_page)
    exam_page.enter_answer("t")
    exam_page.verify_submit_enabled()


@allure.label("tc_id", "11")
@allure.label("priority", "P1")
def test_verify_submit_complete(e2e_page):
    """답안 제출 완료 확인"""
    exam_page = ExamPage(e2e_page)
    exam_page.submit_answer()
    exam_page.verify_submit_complete()


@allure.label("tc_id", "12")
@allure.label("priority", "P1")
def test_open_end_modal(e2e_page):
    """테스트 종료 모달 열기"""
    exam_page = ExamPage(e2e_page)
    exam_page.open_end_modal()
    exam_page.verify_end_modal_open()


@allure.label("tc_id", "13")
@allure.label("priority", "P1")
def test_verify_end_enabled(e2e_page):
    """확인 사항 체크 후 테스트 종료 버튼 활성화"""
    exam_page = ExamPage(e2e_page)
    exam_page.check_end_confirmation()
    exam_page.verify_end_enabled()


@allure.label("tc_id", "14")
@allure.label("priority", "P1")
def test_open_exam_complete(e2e_page):
    """테스트 종료 후 완료 페이지 확인"""
    exam_page = ExamPage(e2e_page)
    exam_page.confirm_end_test()
    complete_page = ExamCompletePage(e2e_page)
    complete_page.verify_loaded()


@allure.label("tc_id", "15")
@allure.label("priority", "P1")
def test_open_exam_result(e2e_page):
    """테스트 결과 페이지 진입"""
    complete_page = ExamCompletePage(e2e_page)
    complete_page.open_result()
    result_page = ExamResultPage(e2e_page)
    result_page.verify_loaded()
