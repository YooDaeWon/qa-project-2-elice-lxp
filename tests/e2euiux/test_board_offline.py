import allure
import pytest

from framework.e2euiux.flows import (
    login_to_main,
    open_classroom_from_main,
)
from framework.e2euiux.pages import (
    BoardListPage,
    BoardWritePage,
)


pytestmark = [
    pytest.mark.board_offline,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


@pytest.fixture(scope="module")
def board_write_page(browser, flow_browser_context_args, credentials):
    """게시물 저장 후 오프라인 상태 유지"""
    context = browser.new_context(**flow_browser_context_args)
    page = context.new_page()

    try:
        login_to_main(page, credentials)

        classroom_page = open_classroom_from_main(page)
        classroom_page.verify_loaded()
        classroom_page.open_board()

        board_list_page = BoardListPage(page)
        board_list_page.verify_loaded()
        board_list_page.open_write()

        write_page = BoardWritePage(page)
        write_page.verify_loaded()
        write_page.fill_title("test spinner")
        write_page.fill_content("test spinner")
        write_page.verify_save_enabled()
        page.context.set_offline(True)
        write_page.save()

        yield write_page
    finally:
        context.close()


@allure.label("tc_id", "43")
@allure.label("priority", "P2")
def test_offline_save_shows_error_toast(board_write_page):
    """네트워크 중단 시 오류 토스트 확인
    *** FAIL 케이스입니다 ***"""
    board_write_page.verify_error_toast()


@allure.label("tc_id", "44")
@allure.label("priority", "P2")
def test_offline_save_hides_spinner(board_write_page):
    """네트워크 중단 시 저장 버튼 복귀 확인
    *** FAIL 케이스입니다 ***"""
    board_write_page.verify_save_spinner()
    board_write_page.verify_save_button_restored()
