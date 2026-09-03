class CourseApi:
    """과목 조회 API"""

    def __init__(self, session, base_url, timeout=5):
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_course(self, headers=None):
        """과목 정보 조회"""
        return self.session.get(
            f"{self.base_url}/acl/course/get/",
            headers=headers,
            timeout=self.timeout,
        )
