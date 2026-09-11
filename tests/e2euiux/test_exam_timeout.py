import allure
import pytest

from framework.e2euiux.flows import (
    login_to_main,
    open_classroom_from_main,
    open_sandbox_for_setup,
)
from framework.e2euiux.pages import (
    ExamNoticePage,
    ExamPage,
    ExamPreparePage,
    ExamTimePage,
)


pytestmark = [
    pytest.mark.exam_timeout,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


def _open_timeout_exam_page(page, credentials):
    """timeout 시험 답안 입력 페이지 열기"""
    login_to_main(page, credentials)

    classroom_page = open_classroom_from_main(page)
    classroom_page.verify_loaded()
    classroom_page.open_learning_subjects()

    course_page = open_sandbox_for_setup(page)
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
    exam_page.verify_timeout_modal()
