"""API 호출 보안성 테스트 전용 fixture 모음

tests/api_security/ 하위 테스트에만 적용되는 conftest.
- .env에서 계정/호스트 정보 로드
- Playwright APIRequestContext 생성 (호스트별)
- 학습자/교육자 토큰 발급 fixture 제공
"""

import os

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from framework.api_security.pages.account_api import AccountApi

load_dotenv()


# ---------------------------------------------------------------------------
# 환경변수 (호스트)
# ---------------------------------------------------------------------------
ACCOUNT_API_URL = os.getenv(
    "ACCOUNT_API_URL", "https://dev-qatrack-account-api.dev.elicer.io"
)
CLASSROOM_API_URL = os.getenv(
    "CLASSROOM_API_URL", "https://dev-qatrack-classroom-api.dev.elicer.io"
)
DASHBOARD_API_URL = os.getenv(
    "DASHBOARD_API_URL", "https://dev-qatrack-dashboard-api.dev.elicer.io"
)
LXP_API_URL = os.getenv("API_BASE_URL", "https://dev-qatrack-api.dev.elicer.io")
ORG_NAME = os.getenv("ORG_NAME", "academy")


# ---------------------------------------------------------------------------
# 환경변수 (계정)
# ---------------------------------------------------------------------------
STUDENT_ID = os.getenv("ST_ID")
STUDENT_PW = os.getenv("ST_PW")
EDUCATOR_ID = os.getenv("TC_ID")
EDUCATOR_PW = os.getenv("TC_PW")
DUMMY_ID = os.getenv("DUMMY_ID")
DUMMY_PW = os.getenv("DUMMY_PW")


@pytest.fixture(scope="session")
def playwright_instance():
    """세션 전체에서 공유하는 Playwright 인스턴스"""
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def api_request(playwright_instance):
    """헤더 없는 순수 APIRequestContext (호스트를 매 요청 full URL로 지정)

    호스트가 4개라 base_url을 고정하지 않고, 각 페이지 객체가 자기 base_url을 들고 요청한다.
    """
    context = playwright_instance.request.new_context()
    yield context
    context.dispose()


@pytest.fixture
def account_api(api_request):
    """account-api(로그인) 페이지 객체"""
    return AccountApi(api_request, ACCOUNT_API_URL)


@pytest.fixture
def student_token(account_api):
    """학습자 계정 access_token 발급 (다른 카테고리 테스트의 인증 기준선)"""
    token = account_api.get_access_token(STUDENT_ID, STUDENT_PW)
    assert token, "학습자 토큰 발급 실패 - .env의 ST_ID/ST_PW를 확인하세요"
    return token


@pytest.fixture
def educator_token(account_api):
    """교육자 계정 access_token 발급"""
    token = account_api.get_access_token(EDUCATOR_ID, EDUCATOR_PW)
    assert token, "교육자 토큰 발급 실패 - .env의 TC_ID/TC_PW를 확인하세요"
    return token
