"""객체권한 BOLA(권한/인가) 보안 테스트 (ID 16~21)

대상: dashboard-api (성적 조회 student, 집계 통계 histogram)
검증 방식: TC의 '기대 결과' 기준. 차단되어야 하는데 뚫리면 실패(빨간불)로 취약점 노출.

BOLA(Broken Object Level Authorization) = 객체 단위 권한 검사 누락.
"요청한 토큰의 주인"과 "조회하려는 리소스의 주인"이 같은지 서버가 확인하지 않는 결함.

주의: 이 카테고리는 대부분 실제 서버가 취약(200 반환)하여 FAIL(빨간불)이 정상 결과.
      취약점을 정직하게 재현·노출하는 것이 이 테스트의 목적이다.
"""

import allure
import pytest

from config.settings import settings
from framework.api_security.pages.dashboard_api import DashboardApi
from utils.assertions import assert_business_rejected, json_body
from tests.api_security.conftest import (
    MY_ACCOUNT_ID,
    OTHER_STUDENT_ID,
)


CLASSROOM_ID = settings.CLASSROOM_ID
COURSE_ID = settings.COURSE_ID

# ID-21: 교육자가 담당하지 않는 타 클래스 UUID (TC 명시값)
OTHER_CLASSROOM_IDS = [
    "10e4be6f-490c-4dee-89c1-ed1d5ee8c613",  # QA6_2팀 클래스
    "84143f2b-92ca-4b82-abb6-e02ee4d1047d",  # 미확인 클래스
]


@allure.epic("API 호출 보안성 테스트")
@allure.feature("객체권한 BOLA")
@pytest.mark.sec_bola
class TestBola:
    """객체권한 BOLA 카테고리 보안 검증 (ID 16~21)"""

    # -- ID 16 ---------------------------------------------------------------
    @allure.title("ID-16 본인 성적 정상 조회 (기준선)")
    def test_id16_본인_성적_정상조회(self, student_client):
        """본인({{my_id}}) 성적은 정상 조회되어야 함 (200) - 타인 차단 판정의 기준선"""
        dashboard = DashboardApi(student_client)
        response = dashboard.get_student(MY_ACCOUNT_ID, CLASSROOM_ID, COURSE_ID)

        assert response.status_code == 200, (
            f"본인 성적 조회인데 200이 아님 (status={response.status_code})"
        )

    # -- ID 17 ---------------------------------------------------------------
    @allure.title("ID-17 타인 성적 직접 조회 차단(수강생)")
    def test_id17_타인_성적_조회_차단(self, student_client):
        """학생 토큰으로 URL의 id만 타인으로 바꿔 접근 시 차단되어야 함 (403/404)

        [기대] 403 또는 404 차단
        [실제] 200 + 타인 개인정보/성적 → IDOR 취약점 → FAIL(빨간불)
        """
        dashboard = DashboardApi(student_client)
        response = dashboard.get_student(OTHER_STUDENT_ID, CLASSROOM_ID, COURSE_ID)

        assert_business_rejected(
            response, context="학생 토큰으로 타인 성적 조회(IDOR)"
        )

    # -- ID 18 ---------------------------------------------------------------
    @allure.title("ID-18 ID 순차스캔으로 타인정보 수집 방지")
    def test_id18_id_순차스캔_차단(self, student_client):
        """본인 id ±5 범위를 순차 조회 시 본인 외에는 전부 차단되어야 함

        [기대] ±5 범위 스캔 전부 403/404
        [실제] 본인 외 일부 id(149, 155 등)에서 200 → 대량 열거 취약점 → FAIL
        """
        dashboard = DashboardApi(student_client)
        my_id = int(MY_ACCOUNT_ID)

        leaked = []
        for seq_id in range(my_id - 5, my_id + 6):
            if seq_id == my_id:
                continue  # 본인은 정상 조회되므로 제외
            response = dashboard.get_student(seq_id, CLASSROOM_ID, COURSE_ID)
            if response.status_code == 200:
                leaked.append(seq_id)

        assert not leaked, (
            f"순차 스캔으로 본인 외 계정이 노출됨: id={leaked} - "
            "ID 열거만으로 다수 사용자의 개인정보 대량 수집 가능(BOLA)"
        )

    # -- ID 19 ---------------------------------------------------------------
    @allure.title("ID-19 수강생이 전체 성적분포 무단 조회 차단")
    def test_id19_전체_성적분포_무단조회_차단(self, student_client):
        """학생 토큰으로 histogram(test_score) 조회 시 차단되어야 함 (403)

        [기대] 학습자 권한은 403 차단
        [실제] 200 + 클래스 전체 점수분포 → 집계 통계 접근통제 부재 → FAIL
        """
        dashboard = DashboardApi(student_client)
        response = dashboard.get_histogram(CLASSROOM_ID, "test_score")

        assert_business_rejected(
            response, context="학생 토큰으로 전체 성적분포(histogram) 조회"
        )

    # -- ID 20 ---------------------------------------------------------------
    @allure.title("ID-20 통계유형 변경 우회 호출 차단")
    def test_id20_통계유형_변경_우회_차단(self, student_client):
        """stats_type을 practice_score로 바꿔도 차단되어야 함 (403)

        [기대] 유형을 바꿔도 모두 403 차단
        [실제] practice_score도 200 → 특정 값이 아닌 API 전체에 권한검사 부재 → FAIL
        (progress는 422로 미지원 유형이므로, 지원 유형인 practice_score로 검증)
        """
        dashboard = DashboardApi(student_client)
        response = dashboard.get_histogram(CLASSROOM_ID, "practice_score")

        assert_business_rejected(
            response, context="학생 토큰으로 practice_score 통계 조회"
        )

    # -- ID 21 ---------------------------------------------------------------
    @allure.title("ID-21 교육자의 비담당 클래스 통계 조회 차단")
    def test_id21_교육자_비담당클래스_통계_차단(self, educator_client):
        """교육자 토큰으로 담당하지 않는 타 클래스 histogram 조회 시 차단되어야 함

        [기대] 담당 아닌 클래스는 403/404 차단
        [실제] 200 + 실데이터 → 접근통제가 프론트에만 있고 백엔드 부재 → FAIL
        웹 UI는 "권한 없음"으로 막지만 API 직접호출은 통과하는 것을 검증.
        """
        dashboard = DashboardApi(educator_client)

        leaked = []
        for other_classroom_id in OTHER_CLASSROOM_IDS:
            response = dashboard.get_histogram(other_classroom_id, "test_score")
            if response.status_code == 200:
                leaked.append(other_classroom_id)

        assert not leaked, (
            f"교육자가 비담당 클래스 통계에 접근됨: {leaked} - "
            "classroom_id만 알면 임의 클래스 통계 열람 가능(BOLA, 백엔드 인가 부재)"
        )
