"""API 호출 보안성 테스트 공통 모듈

Playwright의 APIRequestContext를 감싸 4개 대상 호스트(account/classroom/dashboard/lxp)로의
요청과, 대상 프로그램의 응답 봉투(_result / fail_code) 판정을 공통으로 처리한다.
UI POM이 page를 주입받는 것과 동일한 패턴으로, 여기서는 api_context(APIRequestContext)를 주입받는다.
"""

import json


class BaseApi:
    """보안 API 테스트용 공통 요청 래퍼"""

    def __init__(self, api_context, base_url):
        self.api = api_context
        self.base_url = base_url.rstrip("/")

    def _url(self, path):
        """base_url과 경로를 합쳐 전체 URL 생성"""
        if path.startswith("http"):
            return path
        return self.base_url + "/" + path.lstrip("/")

    def get(self, path, headers=None, params=None):
        """GET 요청"""
        return self.api.get(self._url(path), headers=headers or {}, params=params or {})

    def post(self, path, headers=None, data=None, form=None):
        """POST 요청 (data=JSON 바디, form=form-data 바디)"""
        kwargs = {"headers": headers or {}}
        if data is not None:
            kwargs["data"] = data
        if form is not None:
            kwargs["form"] = form
        return self.api.post(self._url(path), **kwargs)

    def patch(self, path, headers=None, data=None):
        """PATCH 요청"""
        return self.api.patch(self._url(path), headers=headers or {}, data=data or {})

    def delete(self, path, headers=None, data=None):
        """DELETE 요청"""
        return self.api.delete(self._url(path), headers=headers or {}, data=data or {})

    @staticmethod
    def bearer(token):
        """Authorization 헤더 생성"""
        return {"Authorization": "Bearer " + token}

    @staticmethod
    def parse_json(response):
        """응답 body를 JSON(dict)으로 파싱. 실패 시 빈 dict 반환"""
        try:
            return response.json()
        except (json.JSONDecodeError, ValueError):
            return {}

    @classmethod
    def get_fail_code(cls, response):
        """대상 프로그램 실패 응답에서 fail_code(또는 code) 추출

        - account/classroom 계열: 최상위 fail_code 또는 code
        - LXP 계열: _result 봉투 내부에 담기는 경우 대응
        """
        body = cls.parse_json(response)
        if not body:
            return None
        if "fail_code" in body:
            return body["fail_code"]
        if "code" in body:
            return body["code"]
        result = body.get("_result", {})
        if isinstance(result, dict):
            return result.get("fail_code") or result.get("code")
        return None
