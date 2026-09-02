import time


class SafetyKillSwitchError(Exception):
    """안전성 통제 발동"""


class SafetySession:
    """응답 지연과 500 에러를 감시하는 요청 세션"""

    def __init__(self, session, max_latency_ms=5000):
        self.session = session
        self.max_latency_ms = max_latency_ms

    def post(self, url, **kwargs):
        """POST 요청 후 안전성 통제 확인"""
        return self._request("POST", url, **kwargs)

    def get(self, url, **kwargs):
        """GET 요청 후 안전성 통제 확인"""
        return self._request("GET", url, **kwargs)

    def _request(self, method, url, **kwargs):
        start_time = time.time()
        response = self.session.request(method, url, **kwargs)
        latency_ms = (time.time() - start_time) * 1000

        if latency_ms > self.max_latency_ms:
            raise SafetyKillSwitchError(
                f"🚨 [안전성 통제 발동] Latency 5초 초과 감지 ({round(latency_ms)}ms) -> 테스트 즉시 중단"
            )

        if response.status_code == 500:
            raise SafetyKillSwitchError(
                "🚨 [안전성 통제 발동] 500 에러 발생 감지 -> 테스트 즉시 중단"
            )

        return response
