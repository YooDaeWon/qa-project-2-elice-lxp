"""인증·로그인 보안 테스트 (ID 1~6)

대상: account-api (/login/pw)
검증 방식: TC의 '기대 결과'를 기준으로 assert. 보안이 지켜지면 통과,
          취약하면 실패(빨간불)로 결함을 그대로 노출한다.

팀 공통 인프라 재사용:
- 로그인 호출: framework.api_security.pages.AccountClient (팀 APIClient 기반)
- 응답 파싱: utils.assertions.json_body
- Allure 증거 첨부·민감정보 마스킹은 APIClient가 자동 처리

주의: 이 서비스는 인증 실패를 4xx(주로 409) + fail_code 로 응답한다(명세상 401 미정의).
      '차단'은 상태코드 단독이 아니라 '토큰 미발급 + fail_code'로 판정한다.
"""

import allure
import pytest

from framework.api_security.pages.account_client import AccountClient
from utils.assertions import json_body
from tests.api_security.conftest import DUMMY_ID, STUDENT_ID, STUDENT_PW


def _fail_code(response):
    """실패 응답에서 fail_code(또는 code) 추출"""
    try:
        body = response.json()
    except ValueError:
        return None
    return body.get("fail_code") or body.get("code")


@allure.epic("API 호출 보안성 테스트")
@allure.feature("인증·로그인")
@allure.label("owner", "yoodaewon")
@allure.label("team", "QA4")
@pytest.mark.sec_auth_login
class TestAuthLogin:
    """인증·로그인 / 인증강도 카테고리 보안 검증"""

    @allure.title("ID-1 정상 로그인 시 토큰 정상 발급")
    @allure.label("tc_id", "01")
    @allure.label("priority", "P1")
    def test_id01_정상_로그인_토큰_발급(self, account_client):
        """정상 자격증명 로그인 시 200 + access_token(JWT) 발급"""
        response = account_client.login(STUDENT_ID, STUDENT_PW)
        body = json_body(response)

        assert response.status_code == 200, f"정상 로그인인데 status={response.status_code}"
        assert body.get("access_token"), "정상 로그인인데 access_token이 발급되지 않음"

    @allure.title("ID-2 비밀번호 불일치 시 로그인 차단")
    @allure.label("tc_id", "02")
    @allure.label("priority", "P0")
    def test_id02_비밀번호_불일치_차단(self, account_client):
        """비밀번호 틀리면 토큰 미발급 (인증 실패 4xx 또는 200+fail_code)"""
        response = account_client.login(STUDENT_ID, "wrong_password_xyz")
        body = json_body(response)

        assert not body.get("access_token"), "비밀번호 불일치인데 토큰이 발급됨"
        assert response.status_code >= 400 or _fail_code(response), "실패 신호 없음"

    @allure.title("ID-3 미가입 계정 로그인 시 계정존재 노출 차단")
    @allure.label("tc_id", "03")
    @allure.label("priority", "P1")
    def test_id03_미가입_계정_존재노출_차단(self, account_client):
        """미가입 계정 로그인 시 토큰 미발급 (ID-2와 동일 응답이어야 함)"""
        response = account_client.login("nonexistent_account@example.com", "random_xyz")
        body = json_body(response)

        assert not body.get("access_token"), "미가입 계정인데 토큰이 발급됨"
        assert response.status_code >= 400 or _fail_code(response), "실패 신호 없음"

    @allure.title("ID-4 공백값 로그인 차단")
    @allure.label("tc_id", "04")
    @allure.label("priority", "P1")
    def test_id04_공백값_로그인_차단(self, account_client):
        """공백 ID/PW는 서버측 검증으로 차단 (주로 422)"""
        response = account_client.login("", "")
        body = json_body(response)

        assert not body.get("access_token"), "공백 입력인데 토큰이 발급됨"
        assert response.status_code >= 400, f"공백 입력인데 차단되지 않음 (status={response.status_code})"

    @allure.title("ID-5 반복 로그인 실패 시 Brute Force 차단")
    @pytest.mark.slow
    @allure.label("tc_id", "05")
    @allure.label("priority", "P0")
    def test_id05_반복실패_bruteforce_차단(self):
        """로그인 반복 실패 임계치 초과 시 차단 (409 + login_failure_limit_exceed)

        실존 더미 계정(DUMMY_ID)에 오답 비밀번호를 10회 이상 연속 전송하여
        무차별 대입(Brute Force)이 차단되는지 검증한다.
        미가입 계정을 쓰면 model_not_found만 반환되어 실패 횟수가 카운트되지 않으므로
        반드시 실존 계정이어야 한다.
        """
        client = AccountClient()

        blocked = False
        last_fail_code = None
        for _ in range(12):
            response = client.login(DUMMY_ID, "wrong_password_attempt")
            last_fail_code = _fail_code(response)
            if last_fail_code == "login_failure_limit_exceed":
                blocked = True
                break

        assert blocked, (
            "반복 로그인 실패가 차단되지 않음 "
            f"(마지막 fail_code={last_fail_code}) - Brute Force 방어 미작동"
        )

    @allure.title("ID-6 가입·미가입 계정 응답 차이 노출 검증")
    @allure.label("tc_id", "06")
    @allure.label("priority", "P1")
    def test_id06_가입미가입_응답차이_노출(self, account_client):
        """가입계정+오답(A)과 미가입계정(B)의 실패 응답이 동일해야 함

        [기대] A·B의 status code + fail_code 동일
        [실제 서버] A=wrong_password / B=model_not_found 로 상이 → 계정 존재 노출 (FAIL)
        취약점이 살아있으면 실패(빨간불)로 결함을 노출한다.
        """
        resp_a = account_client.login(STUDENT_ID, "wrong_password_xyz")
        resp_b = account_client.login("nonexistent_account@example.com", "random_xyz")

        code_a = _fail_code(resp_a)
        code_b = _fail_code(resp_b)

        assert resp_a.status_code == resp_b.status_code, (
            f"상태코드가 다름 (A={resp_a.status_code}, B={resp_b.status_code}) - 계정 존재 여부 노출"
        )
        assert code_a == code_b, (
            f"fail_code가 다름 (A={code_a}, B={code_b}) - "
            "공격자가 응답 차이로 가입 계정을 식별할 수 있음(계정 열거 취약점)"
        )
