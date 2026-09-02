"""인증·로그인 보안 테스트 (ID 1~6)

대상: account-api (https://dev-qatrack-account-api.dev.elicer.io/login/pw)
검증 방식: TC 엑셀의 '기대 결과'를 기준으로 assert.
           보안이 지켜지면 통과, 취약하면 실패(빨간불)로 결함을 그대로 노출한다.

주의: 이 서비스는 인증 실패를 409(Conflict) + fail_code 로 응답한다(명세상 401 미정의).
      따라서 '차단 여부'는 상태코드 단독이 아니라 '토큰 미발급 + fail_code'로 판정한다.
"""

import pytest

from framework.api_security.pages.account_api import AccountApi
from tests.api_security.conftest import (
    ACCOUNT_API_URL,
    DUMMY_ID,
    STUDENT_ID,
    STUDENT_PW,
)


@pytest.mark.sec_auth_login
class TestAuthLogin:
    """인증·로그인 / 인증강도 카테고리 보안 검증"""

    # -- ID 1 ----------------------------------------------------------------
    def test_id01_정상_로그인_토큰_발급(self, account_api):
        """ID-1: 정상 자격증명 로그인 시 200 + access_token(JWT) 발급"""
        response = account_api.login(STUDENT_ID, STUDENT_PW)
        body = account_api.parse_json(response)

        assert response.status == 200, f"정상 로그인인데 status={response.status}"
        assert body.get("access_token"), "정상 로그인인데 access_token이 발급되지 않음"

    # -- ID 2 ----------------------------------------------------------------
    def test_id02_비밀번호_불일치_차단(self, account_api):
        """ID-2: 비밀번호 틀리면 토큰 미발급 (인증 실패 4xx 또는 200+fail_code)"""
        response = account_api.login(STUDENT_ID, "wrong_password_xyz")
        body = account_api.parse_json(response)
        fail_code = account_api.get_fail_code(response)

        # 토큰이 발급되지 않아야 한다 (핵심 판정)
        assert not body.get("access_token"), "비밀번호 불일치인데 토큰이 발급됨"
        # 실패 신호(4xx 또는 fail_code)가 있어야 한다
        assert response.status >= 400 or fail_code, "실패 신호(상태코드/fail_code) 없음"

    # -- ID 3 ----------------------------------------------------------------
    def test_id03_미가입_계정_존재노출_차단(self, account_api):
        """ID-3: 미가입 계정 로그인 시 토큰 미발급 (ID-2와 동일 응답이어야 함)"""
        response = account_api.login("nonexistent_account@example.com", "random_xyz")
        body = account_api.parse_json(response)
        fail_code = account_api.get_fail_code(response)

        assert not body.get("access_token"), "미가입 계정인데 토큰이 발급됨"
        assert response.status >= 400 or fail_code, "실패 신호 없음"

    # -- ID 4 ----------------------------------------------------------------
    def test_id04_공백값_로그인_차단(self, account_api):
        """ID-4: 공백 ID/PW는 서버측 검증으로 차단 (주로 422)"""
        response = account_api.login("", "")
        body = account_api.parse_json(response)

        assert not body.get("access_token"), "공백 입력인데 토큰이 발급됨"
        assert response.status >= 400, (
            f"공백 입력인데 차단되지 않음 (status={response.status})"
        )

    # -- ID 5 ----------------------------------------------------------------
    @pytest.mark.slow
    def test_id05_반복실패_bruteforce_차단(self, api_request):
        """ID-5: 로그인 반복 실패 임계치 초과 시 차단 (409 + login_failure_limit_exceed)

        더미 계정으로 오답 비밀번호를 10회 이상 연속 전송하여
        무차별 대입(Brute Force)이 차단되는지 검증한다.
        기존 계정을 쓰면 실제 잠금이 걸릴 수 있어 더미 계정을 사용한다.
        """
        account = AccountApi(api_request, ACCOUNT_API_URL)

        blocked = False
        last_fail_code = None
        for _ in range(12):
            response = account.login(DUMMY_ID, "wrong_password_attempt")
            last_fail_code = account.get_fail_code(response)
            if last_fail_code == "login_failure_limit_exceed":
                blocked = True
                break

        assert blocked, (
            "반복 로그인 실패가 차단되지 않음 "
            f"(마지막 fail_code={last_fail_code}) - Brute Force 방어 미작동"
        )

    # -- ID 6 ----------------------------------------------------------------
    def test_id06_가입미가입_응답차이_노출(self, account_api):
        """ID-6: 가입계정+오답(A)과 미가입계정(B)의 실패 응답이 동일해야 함

        [기대] A·B의 status code + fail_code + message가 동일
        [실제 서버] A=wrong_password / B=model_not_found 로 상이 → 계정 존재 노출 (FAIL)
        이 테스트는 취약점이 살아있으면 실패(빨간불)로 결함을 노출한다.
        """
        # A: 가입계정 + 틀린 비밀번호
        resp_a = account_api.login(STUDENT_ID, "wrong_password_xyz")
        # B: 미가입계정 + 임의 비밀번호
        resp_b = account_api.login("nonexistent_account@example.com", "random_xyz")

        code_a = account_api.get_fail_code(resp_a)
        code_b = account_api.get_fail_code(resp_b)

        assert resp_a.status == resp_b.status, (
            f"상태코드가 다름 (A={resp_a.status}, B={resp_b.status}) - 계정 존재 여부 노출"
        )
        assert code_a == code_b, (
            f"fail_code가 다름 (A={code_a}, B={code_b}) - "
            "공격자가 응답 차이로 가입 계정을 식별할 수 있음(계정 열거 취약점)"
        )
