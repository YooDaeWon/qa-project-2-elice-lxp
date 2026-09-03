"""API 호출 보안성 테스트 전용 fixture 모음

tests/api_security/ 하위 테스트에만 적용된다.
팀 공통 인프라(config.settings, clients.api_client)를 재사용하고,
보안 테스트 고유의 로그인/토큰 발급 fixture를 제공한다.
"""

import os

import pytest

from clients.api_client import APIClient
from config.settings import settings
from framework.api_security.pages.account_client import AccountClient


# ---------------------------------------------------------------------------
# 보안 테스트 계정 (팀 settings에 없는 항목은 .env에서 직접 로드)
# ---------------------------------------------------------------------------
# 로그인 자격증명 (이메일 형태)
STUDENT_LOGIN_ID = os.getenv("ST_ID")
STUDENT_PW = os.getenv("ST_PW")
EDUCATOR_LOGIN_ID = os.getenv("TC_ID")
EDUCATOR_PW = os.getenv("TC_PW")

# 하위 호환용 별칭 (기존 test_auth_login.py가 STUDENT_ID를 로그인 이메일로 사용)
STUDENT_ID = STUDENT_LOGIN_ID

# 실존 더미 계정 (Brute Force 등 반복 실패 검증용 - 잠겨도 무방한 계정)
DUMMY_ID = os.getenv("DUMMY_ID")
DUMMY_PW = os.getenv("DUMMY_PW")

# 숫자 계정 ID (성적/BOLA 등 리소스 경로에 쓰는 account_id) - 팀 settings 재사용
MY_ACCOUNT_ID = settings.STUDENT_ID          # 본인 숫자 id (예: 150)
OTHER_STUDENT_ID = settings.OTHER_STUDENT_ID  # 타인 숫자 id (예: 177)


@pytest.fixture
def account_client():
    """account-api 로그인 클라이언트 (토큰 없이 익명 호출)"""
    return AccountClient()


@pytest.fixture
def student_token(account_client):
    """학습자 access_token 발급 (다른 카테고리 테스트의 인증 기준선)"""
    token = account_client.get_access_token(STUDENT_ID, STUDENT_PW)
    assert token, "학습자 토큰 발급 실패 - .env의 ST_ID/ST_PW를 확인하세요"
    return token


@pytest.fixture
def educator_token(account_client):
    """교육자 access_token 발급"""
    token = account_client.get_access_token(EDUCATOR_LOGIN_ID, EDUCATOR_PW)
    assert token, "교육자 토큰 발급 실패 - .env의 TC_ID/TC_PW를 확인하세요"
    return token


@pytest.fixture
def student_client(student_token):
    """학습자 토큰이 주입된 공통 APIClient (권한/BOLA 등 인증 필요 테스트용)"""
    return APIClient(token=student_token, role="student")


@pytest.fixture
def educator_client(educator_token):
    """교육자 토큰이 주입된 공통 APIClient"""
    return APIClient(token=educator_token, role="educator")
