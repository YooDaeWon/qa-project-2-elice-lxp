import requests

from config.settings import settings
from utils.allure_report import (
    api_step,
    attach_exception,
    attach_request,
    attach_response,
)


class APIClient:
    def __init__(self, token: str = "", timeout: int = 20, role: str = "unknown"):
        self.timeout = timeout
        self.role = role
        self.trace_allure = True
        self.session = requests.Session()

        if token:
            auth_value = f"{settings.AUTH_PREFIX}{token}"

            if settings.AUTH_COOKIE_NAME:
                self.session.cookies.set(settings.AUTH_COOKIE_NAME, auth_value)
            elif settings.AUTH_HEADER:
                self.session.headers.update({
                    settings.AUTH_HEADER: auth_value
                })

        self.session.headers.update({"Accept": "application/json"})

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """실제 API 호출을 수행하고, Allure 사용 시 요청/응답 증거를 안전하게 첨부한다."""
        kwargs.setdefault("timeout", self.timeout)

        headers = dict(kwargs.pop("headers", {}) or {})
        if settings.ORG and "x-elice-org-name-short" not in {
            key.lower(): value for key, value in headers.items()
        }:
            headers["x-elice-org-name-short"] = settings.ORG

        if headers:
            kwargs["headers"] = headers

        if not self.trace_allure:
            return self.session.request(method, url, **kwargs)

        with api_step(self.role, method, url):
            attach_request(
                role=self.role,
                method=method,
                url=url,
                kwargs=kwargs,
                org=settings.ORG,
            )
            try:
                response = self.session.request(method, url, **kwargs)
            except Exception as exc:
                attach_exception(exc)
                raise
            attach_response(response)
            return response

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request("POST", url, **kwargs)

    def patch(self, url: str, **kwargs) -> requests.Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        return self.request("DELETE", url, **kwargs)

    def close(self) -> None:
        self.session.close()
