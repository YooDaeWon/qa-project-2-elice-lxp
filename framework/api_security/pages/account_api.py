"""account-api 보안 테스트 페이지 객체

로그인/인증(account-api) 대상의 API 호출을 캡슐화한다.
대상 호스트: https://dev-qatrack-account-api.dev.elicer.io
UI POM(LoginPage)이 page를 받아 화면을 조작하듯, 여기서는 api_context를 받아 API를 호출한다.
"""

from framework.api_security.base_api import BaseApi


class AccountApi(BaseApi):
    """account-api(로그인/인증) 액션 모음"""

    LOGIN_PATH = "/login/pw"
    JSON_HEADER = {"Content-Type": "application/json"}

    def login(self, login_id, password):
        """비밀번호 로그인 요청

        Body: {"login_id": ..., "password": ...}
        정상 시 200 + access_token(JWT), 실패 시 4xx 또는 200+fail_code
        """
        body = {"login_id": login_id, "password": password}
        return self.post(self.LOGIN_PATH, headers=self.JSON_HEADER, data=body)

    def get_access_token(self, login_id, password):
        """로그인 후 응답에서 access_token 추출 (없으면 None)"""
        response = self.login(login_id, password)
        body = self.parse_json(response)
        return body.get("access_token")
