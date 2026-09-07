import secrets

import allure
import pytest

from framework.e2euiux.flows import (
    login_to_main,
    open_classroom_from_main,
    open_sandbox_for_setup,
)
from framework.e2euiux.pages import (
    CoursePage,
    ExamCompletePage,
    ExamNoticePage,
    ExamPage,
    ExamPreparePage,
    ExamResultPage,
)


pytestmark = [
    pytest.mark.exam_retake_flow,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


@pytest.fixture(scope="module")
def retake_answer():
    """재응시 답안용 8자리 랜덤 문자열"""
    return secrets.token_hex(4)


def _open_exam_page(page):
    """시험 응시 페이지 열기"""
    prepare_page = ExamPreparePage(page)
    prepare_page.verify_loaded()
    prepare_page.agree_and_next()

    notice_page = ExamNoticePage(page)
    notice_page.verify_loaded()
    notice_page.start_test()

    exam_page = ExamPage(page)
    exam_page.verify_loaded()


@pytest.fixture(scope="module")
def retake_course_page(e2e_page, credentials):
    """재응시 시험 과목 페이지 상태 준비"""
    login_to_main(e2e_page, credentials)

    classroom_page = open_classroom_from_main(e2e_page)
    classroom_page.verify_loaded()
    classroom_page.open_learning_subjects()

    open_sandbox_for_setup(e2e_page)

    return e2e_page


@allure.label("tc_id", "24")
@allure.label("priority", "P1")
def test_retake_exam(retake_course_page):
    """시험 재응시 버튼 확인"""
    course_page = CoursePage(retake_course_page)
    course_page.retake_test("e2e-retake")
    course_page.verify_retake_available("e2e-retake")


@allure.label("tc_id", "25")
@allure.label("priority", "P1")
def test_submit_retake_exam_shows_result_page(retake_course_page, retake_answer):
    """재응시 답안 제출 후 결과 페이지 확인"""
    course_page = CoursePage(retake_course_page)
    course_page.start_test("e2e-retake")
    _open_exam_page(retake_course_page)

    exam_page = ExamPage(retake_course_page)
    exam_page.enter_answer(retake_answer)
    exam_page.submit_answer()
    exam_page.open_end_modal()
    exam_page.check_end_confirmation()
    exam_page.confirm_end_test()

    complete_page = ExamCompletePage(retake_course_page)
    complete_page.verify_loaded()
    complete_page.open_result()

    result_page = ExamResultPage(retake_course_page)
    result_page.verify_loaded()


@allure.label("tc_id", "26")
@allure.label("priority", "P1")
def test_verify_retake_answer(retake_course_page, retake_answer):
    """재응시 답안 확인"""
    result_page = ExamResultPage(retake_course_page)
    result_page.verify_loaded()
    result_page.open_answers()
    result_page.open_question()
    result_page.verify_answer(retake_answer)
