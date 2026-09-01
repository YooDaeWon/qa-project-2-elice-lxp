import re

import pytest

from framework.e2euiux.pages import (
    ClassroomPage,
    LoginPage,
    MainPage,
    MyClassesPage,
)


pytestmark = pytest.mark.mocking_500

CLASSROOM_API_URL = re.compile(
    r"^https://dev-qatrack-classroom-api\.dev\.elicer\.io/classroom/[^/]+/?$"
)


@pytest.fixture(scope="module")
def classroom_page(e2e_page, credentials):
    """학습자 클래스 페이지 상태 준비"""
    login_page = LoginPage(e2e_page)
    login_page.open()
    login_page.login(
        credentials["user_id"],
        credentials["password"],
    )
    login_page.verify_redirect()

    main_page = MainPage(e2e_page)
    main_page.open_my_classes()

    my_classes_page = MyClassesPage(e2e_page)
    my_classes_page.verify_loaded()
    my_classes_page.open_classroom()

    return ClassroomPage(e2e_page)


@pytest.fixture(scope="module")
def mock_classroom_api(classroom_page):
    """클래스 조회 API 500 응답 설정"""
    page = classroom_page.page
    page.route(
        CLASSROOM_API_URL,
        lambda route: route.fulfill(
            status=500,
            content_type="application/json",
            body="{}",
        ),
    )
    yield classroom_page
    page.unroute(CLASSROOM_API_URL)


def test_id_54_classroom_api_500(mock_classroom_api):
    """ID 54 클래스 조회 API 500 오류 안내 확인"""
    mock_classroom_api.page.reload()
    mock_classroom_api.verify_error_loaded()
    mock_classroom_api.page.wait_for_timeout(10_000)
