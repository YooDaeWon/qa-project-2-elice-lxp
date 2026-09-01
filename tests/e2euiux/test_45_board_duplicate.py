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


pytestmark = pytest.mark.board_duplicate


@pytest.fixture(scope="module")
def board_duplicate_flow(e2e_page, credentials):
    """게시물 중복 요청 테스트 상태 준비"""
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
    initial_count = board_list_page.get_post_count("rapid")
    board_list_page.open_write()

    board_write_page = BoardWritePage(e2e_page)
    board_write_page.verify_loaded()
    board_write_page.fill_title("rapid")
    board_write_page.fill_content("rapid")
    board_write_page.verify_save_enabled()

    return {
        "page": e2e_page,
        "initial_count": initial_count,
    }


def test_id_45_prevent_duplicate_post(board_duplicate_flow):
    """ID 45 게시물 중복 생성 확인"""
    page = board_duplicate_flow["page"]
    board_write_page = BoardWritePage(page)
    board_write_page.save_twice()

    board_post_page = BoardPostPage(page)
    board_post_page.verify_loaded()
    board_post_page.click_board_list()

    board_list_page = BoardListPage(page)
    board_list_page.verify_loaded()
    board_list_page.verify_post_count(
        "rapid",
        board_duplicate_flow["initial_count"] + 1,
    )
