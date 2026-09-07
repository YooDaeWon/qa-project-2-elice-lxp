import os

import allure
import pytest

from framework.e2euiux.pages import LoginPage


pytestmark = [
    pytest.mark.login_flow,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


class _MaskedCredentials(dict):
    """실패 로그에서 로그인 정보 숨김"""

    def __repr__(self):
        return "<masked login exception credentials>"


@pytest.fixture(scope="module")
def login_exception_credentials():
    """로그인 예외 테스트 입력값 준비"""
    return _MaskedCredentials({
        "valid_email": os.environ["VALID_EMAIL"],
        "valid_password": os.environ["VALID_PASSWORD"],
        "invalid_email": os.environ["INVALID_EMAIL"],
        "invalid_password": os.environ["INVALID_PASSWORD"],
        "email_with_spaces": os.environ["EMAIL_WITH_SPACES"],
        "password_with_space": os.environ["PASSWORD_WITH_SPACE"],
    })


@pytest.fixture
def login_exception_page(browser, flow_browser_context_args):
    """케이스별 독립 로그인 페이지 준비"""
    context = browser.new_context(**flow_browser_context_args)
    page = context.new_page()
    login_page = LoginPage(page)
    login_page.open()
    yield login_page
    context.close()


@allure.label("tc_id", "55")
@allure.label("priority", "P2")
def test_invalid_email(
    login_exception_page,
    login_exception_credentials,
):
    """유효하지 않은 아이디 로그인"""
    login_exception_page.fill_login_id(
        login_exception_credentials["invalid_email"]
    )
    login_exception_page.fill_password(
        login_exception_credentials["valid_password"]
    )
    login_exception_page.submit_login()
    login_exception_page.verify_invalid_credentials_message()


@allure.label("tc_id", "56")
@allure.label("priority", "P2")
def test_invalid_password(
    login_exception_page,
    login_exception_credentials,
):
    """유효하지 않은 비밀번호 로그인"""
    login_exception_page.fill_login_id(
        login_exception_credentials["valid_email"]
    )
    login_exception_page.fill_password(
        login_exception_credentials["invalid_password"]
    )
    login_exception_page.submit_login()
    login_exception_page.verify_invalid_credentials_message()


@allure.label("tc_id", "57")
@allure.label("priority", "P2")
def test_empty_email(
    login_exception_page,
    login_exception_credentials,
):
    """아이디 빈 칸 필수 입력 안내"""
    login_exception_page.fill_password(
        login_exception_credentials["valid_password"]
    )
    login_exception_page.submit_login()
    login_exception_page.verify_login_id_required()


@allure.label("tc_id", "58")
@allure.label("priority", "P2")
def test_empty_password(
    login_exception_page,
    login_exception_credentials,
):
    """비밀번호 빈 칸 필수 입력 안내"""
    login_exception_page.fill_login_id(
        login_exception_credentials["valid_email"]
    )
    login_exception_page.submit_login()
    login_exception_page.verify_password_required()


@allure.label("tc_id", "59")
@allure.label("priority", "P2")
def test_login_with_spaces(
    login_exception_page,
    login_exception_credentials,
):
    """아이디 양 옆 공백이 있어도 로그인 성공"""
    login_exception_page.fill_login_id(
        login_exception_credentials["email_with_spaces"]
    )
    login_exception_page.fill_password(
        login_exception_credentials["valid_password"]
    )
    login_exception_page.submit_login()
    login_exception_page.verify_redirect()
    login_exception_page.verify_login_success()


@allure.label("tc_id", "60")
@allure.label("priority", "P2")
def test_password_add_space(
    login_exception_page,
    login_exception_credentials,
):
    """비밀번호 뒤 공백이 있는 로그인"""
    login_exception_page.fill_login_id(
        login_exception_credentials["valid_email"]
    )
    login_exception_page.fill_password(
        login_exception_credentials["password_with_space"]
    )
    login_exception_page.submit_login()
    login_exception_page.verify_invalid_credentials_message()
