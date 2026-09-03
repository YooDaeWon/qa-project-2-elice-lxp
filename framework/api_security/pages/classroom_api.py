"""classroom-api 보안 테스트 페이지 객체 (권한상승 등)

클래스 리소스에 대한 PATCH/POST 및 재조회(GET)를 캡슐화한다.
토큰이 주입된 팀 APIClient를 받아, 권한 밖 필드 주입·Method 변조 등을 시도한다.
대상 호스트: classroom-api
"""

from config.settings import settings


class ClassroomApi:
    """classroom-api 액션 (조회/수정/우회 시도)"""

    def __init__(self, api_client):
        self.api = api_client
        self.base = settings.CLASSROOM_API_BASE_URL.rstrip("/")

    def get_classroom(self, classroom_id):
        """클래스 정보 조회 (PATCH 주입값 반영 여부 재확인용)"""
        return self.api.get(f"{self.base}/classroom/{classroom_id}")

    def get_classroom_without_org(self, classroom_id):
        """org 헤더를 제거하고 클래스 조회 (기관 격리 우회 검증용)

        x-elice-org-name-short를 None으로 주면 팀 APIClient의 org 자동주입이 막히고,
        requests가 값 None 헤더를 전송하지 않아 실제로 org 헤더가 제거된다.
        """
        return self.api.get(
            f"{self.base}/classroom/{classroom_id}",
            headers={"x-elice-org-name-short": None},
        )

    def get_classroom_with_org(self, classroom_id, org_value):
        """지정한 org 값으로 클래스 조회 (타기관 org 변조 검증용)"""
        return self.api.get(
            f"{self.base}/classroom/{classroom_id}",
            headers={"x-elice-org-name-short": org_value},
        )

    def patch_classroom(self, classroom_id, payload):
        """클래스 정보 수정 요청 (권한 밖 필드 주입 시도)"""
        return self.api.patch(
            f"{self.base}/classroom/{classroom_id}",
            json=payload,
        )

    def post_with_method_override(self, classroom_id, override_method, payload):
        """POST에 X-HTTP-Method-Override 헤더를 실어 실제 메서드를 바꿔치기 시도"""
        return self.api.post(
            f"{self.base}/classroom/{classroom_id}",
            headers={"X-HTTP-Method-Override": override_method},
            json=payload,
        )
