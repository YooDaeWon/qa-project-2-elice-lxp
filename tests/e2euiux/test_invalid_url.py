import allure
import pytest

from framework.e2euiux.pages import LoginPage, NotFoundPage


pytestmark = [
    pytest.mark.invalid_url,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


@pytest.fixture(scope="module")
def lxp_page(e2e_page, credentials):
    """LXP 메인 페이지 상태 준비"""
    login_page = LoginPage(e2e_page)
    login_page.open()
    login_page.login(
        credentials["user_id"],
        credentials["password"],
    )
    login_page.verify_redirect()
    return e2e_page


@allure.label("tc_id", "49")
@allure.label("priority", "P1")
def test_open_invalid_url(lxp_page):
    """ID 49 존재하지 않는 URL 오류 화면 확인"""
    not_found_page = NotFoundPage(lxp_page)
    not_found_page.open_invalid_url()
    not_found_page.verify_loaded()
