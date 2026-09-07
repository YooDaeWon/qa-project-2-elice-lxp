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
    pytest.mark.board_title_limit,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]

TITLE_VALUE = "a" * 128


@pytest.fixture(scope="module")
def board_title_page(e2e_page, credentials):
    """게시물 제목 입력 페이지 상태 준비"""
    login_to_main(e2e_page, credentials)

    classroom_page = open_classroom_from_main(e2e_page)
    classroom_page.verify_loaded()
    classroom_page.open_board()

    board_list_page = BoardListPage(e2e_page)
    board_list_page.verify_loaded()
    board_list_page.open_write()

    board_write_page = BoardWritePage(e2e_page)
    board_write_page.verify_loaded()

    return e2e_page


@allure.label("tc_id", "46")
@allure.label("priority", "P2")
def test_limit_board_title(board_title_page):
    """게시물 제목 최대 길이 확인"""
    board_write_page = BoardWritePage(board_title_page)
    board_write_page.fill_title(TITLE_VALUE)
    board_write_page.append_title("test")
    board_write_page.verify_title_limit(TITLE_VALUE)
