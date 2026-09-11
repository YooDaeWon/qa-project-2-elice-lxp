import secrets

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
    notice_page = open_exam_notice(page)
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
    """새로고침 후 답안 자동 저장 확인
    *** FAIL 케이스입니다 ***"""
    login_to_main(e2e_page, credentials)

    classroom_page = open_classroom_from_main(e2e_page)
    classroom_page.verify_loaded()
    classroom_page.open_learning_subjects()

    course_page = open_sandbox_for_setup(e2e_page)
    course_page.start_test("e2e-01")
    _open_exam_page(e2e_page)

    exam_page = ExamPage(e2e_page)
    exam_page.enter_answer(auto_save_answer)
    e2e_page.reload()
    exam_page.verify_loaded()
    exam_page.verify_answer_saved(auto_save_answer)
