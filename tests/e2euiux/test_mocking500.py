import re

import allure
import pytest

from framework.e2euiux.flows import (
    login_to_main,
    open_classroom_from_main,
)


pytestmark = [
    pytest.mark.mocking500,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]

CLASSROOM_API_URL = re.compile(
    r"^https://dev-qatrack-classroom-api\.dev\.elicer\.io/classroom/[^/]+/?$"
)


@pytest.fixture(scope="module")
def classroom_page(e2e_page, credentials):
    """학습자 클래스 페이지 상태 준비"""
    login_to_main(e2e_page, credentials)

    return open_classroom_from_main(e2e_page)


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


@allure.label("tc_id", "54")
@allure.label("priority", "P2")
def test_classroom_api_500(mock_classroom_api):
    """클래스 조회 API 500 오류 안내 확인"""
    mock_classroom_api.page.reload()
    mock_classroom_api.verify_error_loaded()
