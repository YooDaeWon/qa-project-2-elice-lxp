import os

import requests

from .apis import AuthApi, CourseApi, ExamApi


class LoadClient:
    """부하 테스트용 API 세션"""

    def __init__(self, session=None):
        self.session = session or requests.Session()
        base_url = os.getenv(
            "API_BASE_URL",
            "https://dev-qatrack-api.dev.elicer.io",
        ).rstrip("/")
        org_name = os.getenv("ORG_NAME", "academy")
        self.auth = AuthApi(self.session, base_url)
        self.course = CourseApi(self.session, base_url)
        self.exam = ExamApi(self.session, base_url, org_name)
