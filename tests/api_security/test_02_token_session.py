"""토큰·세션 보안 테스트 (ID 7~15)

대상: classroom-api (보호 자원 접근으로 토큰 유효성 검증), account-api (로그인/로그아웃)
검증 방식: TC의 '기대 결과' 기준 assert. 취약하면 실패(빨간불)로 노출.

토큰 무효화 동작(실측 확인):
- 명시적 로그아웃 호출 후 그 토큰 사용 → 409 (무효화됨): ID-7, 8
- 로그아웃 없이 재로그인만 → 이전 토큰 200 (다중세션 허용): ID-9

주의: 이 서비스는 인증 실패를 4xx(주로 409/403) + fail_code 로 응답(명세상 401 미정의).
      차단 판정은 팀 assertions.assert_business_rejected(4xx or 200+내부4xx 종합)로 처리.
"""

import allure
import pytest

from clients.api_client import APIClient
from config.settings import settings
from framework.api_security.pages.account_client import AccountClient
from framework.api_security import token_utils
from utils.assertions import assert_business_rejected, json_body
from tests.api_security.conftest import (
    STUDENT_ID,
    STUDENT_PW,
    OTHER_STUDENT_ID,
)


CLASSROOM_URL = settings.CLASSROOM_API_BASE_URL.rstrip("/")
DASHBOARD_URL = settings.DASHBOARD_API_BASE_URL.rstrip("/")
CLASSROOM_ID = settings.CLASSROOM_ID
ORG = settings.ORG


def _access_classroom(token):
    """주어진 토큰으로 보호 자원(classroom) 접근. 토큰 유효성 판정의 공통 수단."""
    client = APIClient(token=token, role="probe")
    return client.get(f"{CLASSROOM_URL}/classroom/{CLASSROOM_ID}")


@allure.epic("API 호출 보안성 테스트")
@allure.feature("토큰·세션")
@pytest.mark.sec_token_session
class TestTokenSession:
    """토큰·세션 카테고리 보안 검증 (ID 7~15)"""

    # -- ID 7 ----------------------------------------------------------------
    @allure.title("ID-7 로그아웃으로 만료된 토큰 재사용 차단")
    def test_id07_만료_토큰_재사용_차단(self):
        """로그인→로그아웃한 토큰으로 접근 시 차단되어야 함 (409)

        전용 토큰을 새로 발급받아 로그아웃시키므로 다른 테스트의 토큰에 영향 없음.
        """
        account = AccountClient()
        token = account.get_access_token(STUDENT_ID, STUDENT_PW)
        assert token, "테스트용 토큰 발급 실패"

        account.logout(token)  # 이 토큰을 무효화
        response = _access_classroom(token)

        assert_business_rejected(response, context="만료(로그아웃)된 토큰 재사용")

    # -- ID 8 ----------------------------------------------------------------
    @allure.title("ID-8 로그아웃 후 토큰 무효화")
    def test_id08_로그아웃_후_토큰_무효화(self):
        """로그아웃 직후 그 토큰으로 접근 시 즉시 무효화되어 차단되어야 함 (409)"""
        account = AccountClient()
        token = account.get_access_token(STUDENT_ID, STUDENT_PW)
        assert token, "테스트용 토큰 발급 실패"

        logout_response = account.logout(token)
        assert logout_response.status_code == 200, "로그아웃 요청 자체가 실패함"

        response = _access_classroom(token)
        assert_business_rejected(response, context="로그아웃된 토큰 접근")

    # -- ID 9 ----------------------------------------------------------------
    @allure.title("ID-9 재로그인 시 이전 토큰 처리(다중세션 정책)")
    def test_id09_재로그인_이전토큰_다중세션(self):
        """로그아웃 없이 재로그인 시 이전 토큰이 살아있는지 확인 (현재: 다중세션 200)

        TC 기대: 단일세션 정책이면 409 / 200이면 다중세션 허용(정책 확인 필요).
        현재 시스템은 다중세션 허용(200)이 확인된 정책이므로 200을 기대값으로 둔다.
        """
        account = AccountClient()
        token_a = account.get_access_token(STUDENT_ID, STUDENT_PW)  # 첫 토큰
        token_b = account.get_access_token(STUDENT_ID, STUDENT_PW)  # 재로그인(로그아웃 없이)
        assert token_a and token_b, "토큰 발급 실패"

        response = _access_classroom(token_a)  # 이전 토큰으로 접근
        assert response.status_code == 200, (
            f"재로그인 후 이전 토큰이 무효화됨 (status={response.status_code}) - "
            "다중세션 정책과 불일치"
        )

    # -- ID 10 ---------------------------------------------------------------
    @allure.title("ID-10 토큰(JWT) 만료시각(exp) 정보 부재")
    def test_id10_jwt_exp_부재(self, account_client):
        """토큰 payload에 exp(만료) 클레임이 있어야 정상

        [기대] payload에 exp 존재
        [실제] exp 없음 → 무기한 유효(설계 결함) → FAIL(빨간불)
        jwt.io 없이 코드로 payload를 디코딩하여 검증한다.
        """
        token = account_client.get_access_token(STUDENT_ID, STUDENT_PW)
        assert token, "토큰 발급 실패"

        payload = token_utils.decode_payload(token)
        assert "exp" in payload, (
            "토큰 payload에 exp(만료시각) 클레임이 없음 - "
            "탈취 시 기한 없이 악용 가능(설계 결함, refresh token 도입 필요)"
        )

    # -- ID 11 ---------------------------------------------------------------
    @allure.title("ID-11 인증 헤더 없이 접근 차단")
    def test_id11_인증헤더_없이_접근_차단(self):
        """Authorization 헤더 없는 요청은 거부되어야 함 (403 + no_access_token)"""
        # 토큰 없이(익명) classroom 접근
        client = APIClient(role="anonymous")
        response = client.get(f"{CLASSROOM_URL}/classroom/{CLASSROOM_ID}")

        assert_business_rejected(response, context="인증 헤더 없는 접근")

    # -- ID 12 ---------------------------------------------------------------
    @allure.title("ID-12 무효 토큰 인증오류 코드 분류")
    def test_id12_무효토큰_인증오류코드(self):
        """형식이 잘못된 토큰(INVALID123)은 인증 오류(403)로 거부되어야 함

        [기대] 403 (인증 오류)
        [실제] 409 (논리 오류) → 상태코드 분류 불일치 → FAIL(빨간불)
        차단 자체는 정상이나, 명세상 인증오류=403인데 409로 응답하는 오분류를 검증.
        """
        response = _access_classroom("INVALID123")

        # 차단은 되어야 하고(데이터 미반환), 그 상태코드가 403이어야 명세에 맞음
        assert_business_rejected(response, context="무효 토큰")
        assert response.status_code == 403, (
            f"무효 토큰 응답이 403(인증오류)이 아닌 {response.status_code} - "
            "명세상 인증오류는 403인데 논리오류 코드로 오분류됨"
        )

    # -- ID 13 ---------------------------------------------------------------
    @allure.title("ID-13 토큰 서명 변조 시 인증 차단")
    def test_id13_서명_변조_차단(self, account_client):
        """서명(뒤 4글자)만 변조한 토큰은 거부되어야 함 (409, 데이터 미반환)"""
        token = account_client.get_access_token(STUDENT_ID, STUDENT_PW)
        assert token, "토큰 발급 실패"

        tampered = token_utils.tamper_signature(token)
        response = _access_classroom(tampered)

        assert_business_rejected(response, context="서명 변조 토큰")

    # -- ID 14 ---------------------------------------------------------------
    @allure.title("ID-14 토큰 ID 변조로 타인 데이터 접근 차단")
    def test_id14_payload_id_변조_차단(self, account_client):
        """payload의 _id를 타인 값으로 변조한 토큰은 거부되어야 함 (403)

        dashboard-api의 타인 성적 경로에 변조 토큰으로 접근 시도.
        """
        token = account_client.get_access_token(STUDENT_ID, STUDENT_PW)
        assert token, "토큰 발급 실패"
        assert OTHER_STUDENT_ID, ".env에 OTHER_STUDENT_ID가 필요합니다"

        tampered = token_utils.tamper_payload(
            token, _id=OTHER_STUDENT_ID, account_id=OTHER_STUDENT_ID
        )
        client = APIClient(token=tampered, role="probe")
        response = client.get(
            f"{DASHBOARD_URL}/student/{OTHER_STUDENT_ID}",
            params={"classroom_id": CLASSROOM_ID},
        )

        assert_business_rejected(response, context="_id 변조 토큰 타인 데이터 접근")

    # -- ID 15 ---------------------------------------------------------------
    @allure.title("ID-15 토큰 서명검증 무력화(alg:none) 차단")
    def test_id15_alg_none_차단(self, account_client):
        """alg를 none으로 낮추고 서명을 제거한 토큰은 거부되어야 함 (403/409)"""
        token = account_client.get_access_token(STUDENT_ID, STUDENT_PW)
        assert token, "토큰 발급 실패"

        alg_none = token_utils.make_alg_none(token)
        response = _access_classroom(alg_none)

        assert_business_rejected(response, context="alg:none 다운그레이드 토큰")
