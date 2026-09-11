import allure
import pytest

from framework.e2euiux.flows import (
    login_to_main,
    open_classroom_from_main,
)
from framework.e2euiux.pages import (
    BoardListPage,
    BoardPostPage,
    BoardWritePage,
    ClassroomPage,
)


pytestmark = [
    pytest.mark.board_flow,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


@pytest.fixture(scope="module")
def board_e2e_page(e2e_page, credentials):
    """게시판 E2E 시작 상태 준비"""
    login_to_main(e2e_page, credentials)

    classroom_page = open_classroom_from_main(e2e_page)
    classroom_page.verify_loaded()

    return e2e_page


@allure.label("tc_id", "16")
@allure.label("priority", "P1")
def test_open_board(board_e2e_page):
    """게시판 페이지 진입"""
    classroom_page = ClassroomPage(board_e2e_page)
    classroom_page.open_board()

    board_list_page = BoardListPage(board_e2e_page)
    board_list_page.verify_loaded()


@allure.label("tc_id", "17")
@allure.label("priority", "P1")
def test_open_board_write(board_e2e_page):
    """글쓰기 페이지 진입"""
    board_list_page = BoardListPage(board_e2e_page)
    board_list_page.open_write()

    board_write_page = BoardWritePage(board_e2e_page)
    board_write_page.verify_loaded()


@allure.label("tc_id", "18")
@allure.label("priority", "P1")
def test_create_board_post(board_e2e_page):
    """게시물 작성"""
    board_write_page = BoardWritePage(board_e2e_page)
    board_write_page.fill_title("test title")
    board_write_page.fill_content("test")
    board_write_page.append_content(" body")
    board_write_page.verify_save_enabled()
    board_write_page.save()

    board_post_page = BoardPostPage(board_e2e_page)
    board_post_page.verify_loaded()


@allure.label("tc_id", "19")
@allure.label("priority", "P1")
def test_add_comment(board_e2e_page):
    """댓글 작성"""
    board_post_page = BoardPostPage(board_e2e_page)
    previous_count = board_post_page.get_comment_count()
    board_post_page.fill_comment("test comment")
    board_post_page.register_comment()
    board_post_page.verify_comment_added(previous_count, "test comment")


@allure.label("tc_id", "20")
@allure.label("priority", "P2")
def test_prevent_duplicate_comment(board_e2e_page):
    """댓글 중복 작성 확인
    *** FAIL 케이스입니다 ***"""
    board_post_page = BoardPostPage(board_e2e_page)
    previous_count = board_post_page.get_comment_count()
    board_post_page.fill_comment("rapid")
    board_post_page.register_comment_twice()
    board_post_page.verify_single_comment_after_double_click(
        previous_count,
        "rapid",
    )
