class SafetyKillSwitchError(Exception):
    """안전성 통제 발동"""


class SafetySession:
    """HTTP 500 에러를 감시하는 요청 세션"""

    def __init__(self, session):
        self.session = session

    def post(self, url, **kwargs):
        """POST 요청 후 안전성 통제 확인"""
        return self._request("POST", url, **kwargs)

    def get(self, url, **kwargs):
        """GET 요청 후 안전성 통제 확인"""
        return self._request("GET", url, **kwargs)

    def _request(self, method, url, **kwargs):
        response = self.session.request(method, url, **kwargs)

        if response.status_code == 500:
            raise SafetyKillSwitchError(
                "🚨 [안전성 통제 발동] 500 에러 발생 감지 -> 테스트 즉시 중단"
            )

        return response
