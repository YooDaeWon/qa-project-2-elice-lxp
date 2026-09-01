import pytest

from framework.e2euiux.pages import (
    BoardListPage,
    BoardWritePage,
    ClassroomPage,
    LoginPage,
    MainPage,
    MyClassesPage,
)


pytestmark = pytest.mark.board_title_limit

TITLE_VALUE = "a" * 128


@pytest.fixture(scope="module")
def board_title_page(e2e_page, credentials):
    """게시물 제목 입력 페이지 상태 준비"""
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
    classroom_page.open_board()

    board_list_page = BoardListPage(e2e_page)
    board_list_page.verify_loaded()
    board_list_page.open_write()

    board_write_page = BoardWritePage(e2e_page)
    board_write_page.verify_loaded()

    return e2e_page


def test_id_46_limit_board_title(board_title_page):
    """ID 46 게시물 제목 최대 길이 확인"""
    board_write_page = BoardWritePage(board_title_page)
    board_write_page.fill_title(TITLE_VALUE)
    board_write_page.append_title("test")
    board_write_page.verify_title_limit(TITLE_VALUE)
