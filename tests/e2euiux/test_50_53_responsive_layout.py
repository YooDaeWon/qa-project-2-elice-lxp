import allure
import pytest

from framework.e2euiux.pages import LoginPage, MainPage


pytestmark = [
    pytest.mark.responsive_layout,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


def _login(page, credentials):
    """LXP 메인 페이지 로그인"""
    login_page = LoginPage(page)
    login_page.open()
    login_page.login(
        credentials["user_id"],
        credentials["password"],
    )
    login_page.verify_redirect()


@pytest.fixture(scope="module")
def logged_in_page(e2e_page, credentials):
    """로그인된 LXP 메인 페이지 상태 준비"""
    _login(e2e_page, credentials)
    return e2e_page


@pytest.fixture(scope="module")
def mobile_main_page(logged_in_page):
    """모바일 viewport의 메인 페이지 상태 준비"""
    logged_in_page.set_viewport_size({"width": 390, "height": 844})
    logged_in_page.reload()
    return MainPage(logged_in_page)


@pytest.fixture(scope="module")
def tablet_main_page(mobile_main_page):
    """태블릿 viewport의 메인 페이지 상태 준비"""
    mobile_main_page.close_menu()
    mobile_main_page.page.set_viewport_size({"width": 810, "height": 1080})
    return mobile_main_page


@allure.label("tc_id", "50")
@allure.label("priority", "P2")
def test_id_50_mobile_menu_button(mobile_main_page):
    """ID 50 모바일 햄버거 버튼 표시 확인"""
    mobile_main_page.verify_menu_button_visible()


@allure.label("tc_id", "51")
@allure.label("priority", "P2")
def test_id_51_mobile_open_menu(mobile_main_page):
    """ID 51 모바일 전체 메뉴 표시 확인"""
    mobile_main_page.open_menu()
    mobile_main_page.verify_menu_visible()


@allure.label("tc_id", "52")
@allure.label("priority", "P2")
def test_id_52_tablet_menu_button(tablet_main_page):
    """ID 52 태블릿 햄버거 버튼 표시 확인"""
    tablet_main_page.verify_menu_button_visible()


@allure.label("tc_id", "53")
@allure.label("priority", "P2")
def test_id_53_tablet_open_menu(tablet_main_page):
    """ID 53 태블릿 전체 메뉴 표시 확인"""
    tablet_main_page.open_menu()
    tablet_main_page.verify_menu_visible()
