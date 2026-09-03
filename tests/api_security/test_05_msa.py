"""MSA/아키텍처 보안 테스트 (ID 25~29)

대상: classroom-api, dashboard-api (마이크로서비스 간 인가 일관성)
검증 방식: TC의 '기대 결과' 기준. 기관 격리·서비스 간 인가 불일치가 뚫리면 실패(빨간불).

MSA(Microservice Architecture) 보안 이슈:
- 멀티테넌시 격리: org 헤더로 기관을 구분하는데, 헤더 부재 시 검사가 생략되면 격리 우회
- 서비스 간 인가 불일치: 같은 리소스인데 서비스마다 권한 검사가 달라 우회 경로 발생
"""

import allure
import pytest

from config.settings import settings
from framework.api_security.pages.classroom_api import ClassroomApi
from framework.api_security.pages.dashboard_api import DashboardApi
from utils.assertions import assert_business_rejected, is_business_rejected, json_body


CLASSROOM_ID = settings.CLASSROOM_ID
COURSE_ID = settings.COURSE_ID

# 비소속(타) 클래스 UUID (TC 명시값)
OTHER_CLASSROOM_ID = "84143f2b-92ca-4b82-abb6-e02ee4d1047d"


@allure.epic("API 호출 보안성 테스트")
@allure.feature("MSA/아키텍처")
@pytest.mark.sec_msa
class TestMsaArchitecture:
    """MSA/아키텍처 카테고리 보안 검증 (ID 25~29)"""

    # -- ID 25 ---------------------------------------------------------------
    @allure.title("ID-25 타 기관·타 클래스 리소스 접근 차단")
    def test_id25_타클래스_리소스_접근_차단(self, student_client):
        """학생 토큰으로 비소속 클래스 접근 시 차단되어야 함 (403/404 또는 fail_code)"""
        classroom = ClassroomApi(student_client)
        response = classroom.get_classroom(OTHER_CLASSROOM_ID)

        assert_business_rejected(response, context="비소속 클래스 접근")

    # -- ID 26 ---------------------------------------------------------------
    @allure.title("ID-26 org 헤더 없이 타기관 접근")
    def test_id26_org헤더_없이_접근_차단(self, student_client):
        """org 헤더를 제거하면 요청이 거부되어야 함 (400/401/403)

        [기대] org 헤더 부재 시 차단
        [실제] 200 + 클래스 데이터 → 헤더 부재 시 기관 격리 검사 생략 → FAIL(빨간불)
        (ID-27과 함께: 틀린 org는 409 차단인데 org를 아예 빼면 200 통과하는 로직 허점)
        """
        classroom = ClassroomApi(student_client)
        response = classroom.get_classroom_without_org(CLASSROOM_ID)

        assert_business_rejected(response, context="org 헤더 제거 후 접근")

    # -- ID 27 ---------------------------------------------------------------
    @allure.title("ID-27 org 헤더 변조로 타기관 접근 차단")
    def test_id27_org헤더_변조_접근_차단(self, student_client):
        """존재하지 않는/타 기관 org 값으로 요청 시 차단되어야 함 (403/404/409)

        두 가지 변조값(nonexistent_org_xyz, default)을 모두 검증한다.
        타기관 org로 데이터가 반환되면 교차기관 접근(Critical).
        """
        classroom = ClassroomApi(student_client)

        for org_value in ["nonexistent_org_xyz", "default"]:
            response = classroom.get_classroom_with_org(CLASSROOM_ID, org_value)
            assert is_business_rejected(response), (
                f"변조 org='{org_value}'로 데이터가 반환됨 (status={response.status_code}) - "
                "교차기관 접근 차단 실패"
            )

    # -- ID 28 ---------------------------------------------------------------
    @allure.title("ID-28 서비스 별 권한검사 불일치")
    def test_id28_서비스간_권한검사_불일치(self, student_client):
        """같은 비소속 클래스를 classroom-api와 dashboard-api에 각각 요청

        [기대] 모든 서비스가 동일하게 차단
        [실제] classroom은 403 차단 / dashboard는 200 통과 → 서비스 간 불일치 → FAIL
        한 서비스라도 인가가 빠져 우회 경로가 되면 구조적 결함이다.
        """
        classroom = ClassroomApi(student_client)
        dashboard = DashboardApi(student_client)

        classroom_resp = classroom.get_classroom(OTHER_CLASSROOM_ID)
        dashboard_resp = dashboard.get_histogram(OTHER_CLASSROOM_ID, "test_score")

        classroom_blocked = is_business_rejected(classroom_resp)
        dashboard_blocked = is_business_rejected(dashboard_resp)

        # 두 서비스의 차단 여부가 일치해야 정상 (하나만 뚫리면 우회 경로)
        assert classroom_blocked == dashboard_blocked, (
            "서비스 간 권한검사 불일치 - "
            f"classroom 차단={classroom_blocked}(status={classroom_resp.status_code}), "
            f"dashboard 차단={dashboard_blocked}(status={dashboard_resp.status_code}). "
            "한 서비스에만 인가가 빠져 우회 경로가 됨(구조적 결함)"
        )

    # -- ID 29 ---------------------------------------------------------------
    @allure.title("ID-29 존재하지 않는 리소스 상태코드 분류")
    def test_id29_없는리소스_상태코드_정합성(self, educator_client):
        """존재하지 않는 student id(99999) 조회 시 404로 응답해야 함

        [기대] 404 Not Found
        [실제] 409 Conflict + code=model_not_found → 상태코드 오분류 → FAIL(빨간불)
        보안 침해는 아니나, "없음"을 "충돌(409)"로 응답하는 HTTP 규약 불일치.
        """
        dashboard = DashboardApi(educator_client)
        response = dashboard.get_student(99999, CLASSROOM_ID, COURSE_ID)

        assert response.status_code == 404, (
            f"존재하지 않는 리소스 응답이 404가 아닌 {response.status_code} - "
            "'없음'을 '충돌(409)'로 오분류(HTTP 규약 불일치, API 정합성 이슈)"
        )
