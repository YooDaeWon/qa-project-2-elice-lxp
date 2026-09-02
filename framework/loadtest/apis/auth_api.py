class AuthApi:
    """로그인 API"""

    def __init__(self, session, base_url, timeout=5):
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def login(self, login_id, password):
        """아이디와 비밀번호로 로그인"""
        return self.session.post(
            f"{self.base_url}/global/auth/login/",
            json={"login_id": login_id, "password": password},
            timeout=self.timeout,
        )

    def extract_token(self, response):
        """로그인 응답에서 세션 토큰 추출"""
        data = response.json()
        return data.get("eliceSessionKey") or data.get("token")
