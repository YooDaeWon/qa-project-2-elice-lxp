import allure
import pytest

from framework.e2euiux.flows import (
    login_to_main,
    open_classroom_from_main,
    open_exam_notice,
    open_sandbox_for_setup,
)
from framework.e2euiux.pages import ExamPage


pytestmark = [
    pytest.mark.exam_offline,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


def _open_exam_page(page, credentials):
    """답안 입력 페이지까지 열기"""
    login_to_main(page, credentials)

    classroom_page = open_classroom_from_main(page)
    classroom_page.verify_loaded()
    classroom_page.open_learning_subjects()

    course_page = open_sandbox_for_setup(page)

    course_page.start_test("e2e-01")

    notice_page = open_exam_notice(page)
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
