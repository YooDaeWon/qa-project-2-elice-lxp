"""dashboard-api 보안 테스트 페이지 객체 (BOLA 카테고리)

성적 조회(student) 및 집계 통계(histogram) 접근을 캡슐화한다.
토큰이 주입된 팀 APIClient를 받아, 그 토큰으로 대상 리소스에 접근한다.
대상 호스트: dashboard-api
"""

from config.settings import settings


class DashboardApi:
    """dashboard-api 조회 액션 (성적/통계)"""

    def __init__(self, api_client):
        # 토큰이 주입된 APIClient (student_client / educator_client)
        self.api = api_client
        self.base = settings.DASHBOARD_API_BASE_URL.rstrip("/")

    def get_student(self, student_id, classroom_id, course_id):
        """특정 학생의 성적/개인정보 조회

        본인 id면 정상(200), 타인 id로 바꿔도 차단되어야 함(IDOR 검증).
        """
        return self.api.get(
            f"{self.base}/student/{student_id}",
            params={"classroom_id": classroom_id, "course_id": course_id},
        )

    def get_histogram(self, classroom_id, stats_type):
        """클래스 전체 점수분포(집계 통계) 조회

        교육자 전용이어야 하며, 학습자나 비담당 교육자는 차단되어야 함.
        stats_type: test_score / practice_score / progress
        """
        return self.api.get(
            f"{self.base}/histogram",
            params={"classroom_id": classroom_id, "stats_type": stats_type},
        )
