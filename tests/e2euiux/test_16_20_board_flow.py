import pytest

from framework.e2euiux.pages import (
    BoardListPage,
    BoardPostPage,
    BoardWritePage,
    ClassroomPage,
    LoginPage,
    MainPage,
    MyClassesPage,
)


pytestmark = pytest.mark.board_flow


@pytest.fixture(scope="module")
def board_e2e_page(e2e_page, credentials):
    """게시판 E2E 시작 상태 준비"""
    login_page = LoginPage(e2e_page)
    login_page.open()
    login_page.login(credentials["user_id"], credentials["password"])
    login_page.verify_redirect()

    main_page = MainPage(e2e_page)
    main_page.open_my_classes()

    my_classes_page = MyClassesPage(e2e_page)
    my_classes_page.verify_loaded()
    my_classes_page.open_classroom()

    classroom_page = ClassroomPage(e2e_page)
    classroom_page.verify_loaded()

    return e2e_page


def test_id_16_open_board(board_e2e_page):
    """ID 16 게시판 페이지 진입"""
    classroom_page = ClassroomPage(board_e2e_page)
    classroom_page.open_board()

    board_list_page = BoardListPage(board_e2e_page)
    board_list_page.verify_loaded()


def test_id_17_open_board_write(board_e2e_page):
    """ID 17 글쓰기 페이지 진입"""
    board_list_page = BoardListPage(board_e2e_page)
    board_list_page.open_write()

    board_write_page = BoardWritePage(board_e2e_page)
    board_write_page.verify_loaded()


def test_id_18_create_board_post(board_e2e_page):
    """ID 18 게시물 작성"""
    board_write_page = BoardWritePage(board_e2e_page)
    board_write_page.fill_title("test title")
    board_write_page.fill_content("test")
    board_write_page.append_content(" body")
    board_write_page.verify_save_enabled()
    board_write_page.save()

    board_post_page = BoardPostPage(board_e2e_page)
    board_post_page.verify_loaded()


def test_id_19_add_comment(board_e2e_page):
    """ID 19 댓글 작성"""
    board_post_page = BoardPostPage(board_e2e_page)
    previous_count = board_post_page.get_comment_count()
    board_post_page.fill_comment("test comment")
    board_post_page.register_comment()
    board_post_page.verify_comment_added(previous_count, "test comment")


def test_id_20_prevent_duplicate_comment(board_e2e_page):
    """ID 20 댓글 중복 작성 확인"""
    board_post_page = BoardPostPage(board_e2e_page)
    previous_count = board_post_page.get_comment_count()
    board_post_page.fill_comment("rapid")
    board_post_page.register_comment_twice()
    board_post_page.verify_comment_added(previous_count, "rapid")
