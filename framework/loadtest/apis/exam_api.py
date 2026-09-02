class ExamApi:
    """시험 입장·제출·재응시 API"""

    COURSE_ID = 45

    def __init__(self, session, base_url, org_name, timeout=5):
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.org_name = org_name
        self.timeout = timeout

    def _url(self, path):
        return f"{self.base_url}/org/{self.org_name}/lecture/test/{path}"

    def enter(self, course_id=None):
        """시험 입장"""
        return self.session.post(
            self._url("enter/"),
            json={"course_id": course_id or self.COURSE_ID},
            timeout=self.timeout,
        )

    def submit(self, course_id=None):
        """답안 제출"""
        return self.session.post(
            self._url("reset/by_self/"),
            json={"course_id": course_id or self.COURSE_ID},
            timeout=self.timeout,
        )

    def reset(self, course_id=None):
        """시험 재응시 초기화"""
        return self.session.post(
            self._url("reset/"),
            json={"course_id": course_id or self.COURSE_ID},
            timeout=self.timeout,
        )
