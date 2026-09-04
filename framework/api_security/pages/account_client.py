"""account-api 로그인 클라이언트 (API 호출 보안성 테스트 전용)

로그인/인증(account-api)은 팀 clients/ 의 기본 호출 범위에 없는 보안 테스트 고유 영역이므로
api_security 영역에서 관리한다. 실제 HTTP 호출은 팀 공통 APIClient를 재사용하여
Allure 증거 첨부·민감정보 마스킹을 그대로 활용한다.

대상 호스트: account-api (로그인 시점엔 토큰이 없고 org 헤더도 불필요)
"""

from clients.api_client import APIClient
from config.settings import settings


class AccountClient:
    """account-api 로그인 액션 모음"""

    LOGIN_PATH = "/login/pw"

    # 로그아웃은 LXP 호스트(API_BASE_URL)의 경로를 사용한다.
    LOGOUT_PATH = "/global/auth/logout/"

    def __init__(self, api_client: APIClient = None):
        # 로그인은 토큰 없이 호출한다. 별도 클라이언트를 주입받지 않으면 새로 생성한다.
        self.api = api_client or APIClient(role="anonymous")
        self.base = (settings.ACCOUNT_API_BASE_URL or "").rstrip("/")
        self.lxp_base = (settings.API_BASE_URL or "").rstrip("/")
        if not self.base.startswith("http"):
            raise RuntimeError(
                f"ACCOUNT_API_BASE_URL이 유효하지 않습니다: {self.base!r}. "
                "https://dev-qatrack-account-api.dev.elicer.io 형태여야 합니다."
            )

    def login(self, login_id, password):
        """비밀번호 로그인 요청

        Body(JSON): {"login_id": ..., "password": ...}
        정상 시 200 + access_token(JWT), 실패 시 4xx 또는 200 + fail_code
        """
        return self.api.post(
            f"{self.base}{self.LOGIN_PATH}",
            json={"login_id": login_id, "password": password},
        )

    def get_access_token(self, login_id, password):
        """로그인 후 응답에서 access_token 추출 (없으면 None)"""
        response = self.login(login_id, password)
        try:
            return response.json().get("access_token")
        except ValueError:
            return None

    def logout(self, token):
        """주어진 토큰으로 로그아웃 요청 (해당 토큰을 서버에서 무효화)

        LXP 호스트의 /global/auth/logout/ 에 Bearer 토큰을 실어 POST.
        응답: 200 + {"_result":{"status":"ok","status_code":200}}
        """
        logout_client = APIClient(token=token, role="logout")
        return logout_client.post(f"{self.lxp_base}{self.LOGOUT_PATH}")
