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

    def delete_member(self, member_id, classroom_id):
        """클래스 구성원 강제 퇴장 요청 (권한 없는 사용자의 타인 퇴출 시도)

        명세에 없는 그림자 API로, 관리 UI의 '구성원 제거' 동작을 HAR로 확보했다.
        삭제 대상은 경로의 member_id, 소속 클래스는 body로 전달한다.
        """
        return self.api.delete(
            f"{self.base}/member/{member_id}",
            json={"classroom_id": classroom_id},
        )

    def add_members(self, classroom_id, account_ids, role="student"):
        """구성원 일괄 등록 요청 (delete_member의 반대 동작)

        명세에 없는 그림자 API로, 관리 UI의 '구성원 등록' 동작을 HAR로 확보했다.
        응답은 task_id만 내려주지만 실제로는 즉시(약 0.2초 내) 반영된다.
        """
        return self.api.post(
            f"{self.base}/member/bulk",
            json={
                "classroom_id": classroom_id,
                "account_ids": list(account_ids),
                "role": role,
            },
        )

    def list_members(self, classroom_id, skip=0, count=100):
        """구성원 전체 목록 조회

        filter_search는 이메일 전체 문자열과 매칭되지 않아(부분/이름 검색 추정),
        특정 account_id를 찾을 때는 전체 목록을 가져와 클라이언트에서 대조한다.
        """
        return self.api.get(
            f"{self.base}/member",
            params={"classroom_id": classroom_id, "skip": skip, "count": count},
        )

    def get_articles(self, classroom_id, skip=0, count=10, filter_title=None):
        """클래스 게시글 목록 조회 (검색어 반사형 XSS 검증용)

        filter_title은 검색어 파라미터로, 입력값이 응답에 실행 가능한 형태로
        되돌아오는지(반사형 XSS) 확인하는 데 사용한다.
        """
        params = {"skip": skip, "count": count}
        if filter_title is not None:
            params["filter_title"] = filter_title
        return self.api.get(
            f"{self.base}/classroom/{classroom_id}/article",
            params=params,
        )

    def options_preflight(self, classroom_id, origin, request_method="GET"):
        """CORS 사전확인(preflight) 요청 (허용 출처 화이트리스트 검증용)

        브라우저가 교차 출처 요청 전에 보내는 OPTIONS를 그대로 재현한다.
        서버가 임의 Origin을 그대로 반사하는지는 응답 헤더로만 판별할 수 있다.
        """
        return self.api.request(
            "OPTIONS",
            f"{self.base}/classroom/{classroom_id}",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": request_method,
            },
        )
