"""비즈니스로직 보안 테스트 (ID 30~36)

대상: classroom-api, LXP(dev-qatrack-api)
검증 방식: TC의 '기대 결과' 기준. 업무 규칙이 서버에서 강제되지 않으면 실패(빨간불).

비즈니스로직 보안 이슈:
- 인가 규칙(권한 회수, 타인 강제퇴장)이 서버에서 즉시 반영되는가
- 업무 규칙(재응시 횟수, 시험 종료 시각)이 클라이언트가 아닌 서버에서 강제되는가
  → 화면에서 막혀 있어도 API를 직접 호출하면 우회되는 경우가 결함이다
"""

import os
import time

import allure
import pytest

from clients.api_client import APIClient
from config.settings import settings
from framework.api_security import token_utils
from framework.api_security.pages.classroom_api import ClassroomApi
from framework.api_security.pages.lxp_api import LxpApi
from utils.assertions import (
    assert_business_rejected,
    assert_http,
    is_business_rejected,
    json_body,
)


CLASSROOM_ID = settings.CLASSROOM_ID

# ID-30 전용 계정 (권한 부여/회수를 반복해도 소모되지 않음 - 다른 테스트와 공유 금지)
WITHDRAW_LOGIN_ID = os.getenv("SEC_WITHDRAW_ID")

# 타 수강생 member_id (HAR로 확보한 구성원 관리 API 경로 파라미터)
OTHER_MEMBER_ID = os.getenv(
    "SEC_OTHER_MEMBER_ID", "acc68a62-b9d5-4802-8c0f-f33769b6bee2"
)

# 재응시 초기화 대상 시험 lecture_id (팀 LECTURE_ID와 용도가 달라 별도 관리)
# 1645는 e2e 팀의 exam_flow 전용 강의(e2e-01)와 공유되어 충돌 위험이 있어
# course_id=732의 미사용 시험 강의 1586("TEST")으로 교체함
RESET_LECTURE_ID = os.getenv("SEC_RESET_LECTURE_ID", "1586")

# 시간 종료된 시험의 문항 id (제출 차단 검증용)
TIMEOUT_QUIZ_ID = os.getenv("SEC_TIMEOUT_QUIZ_ID", "1356")

# 재응시 제한 검증 시 반복 호출 횟수
RESET_ATTEMPT_COUNT = 20


@allure.epic("API 호출 보안성 테스트")
@allure.feature("비즈니스로직")
@allure.label("owner", "yoodaewon")
@allure.label("team", "QA4")
@pytest.mark.sec_business
class TestBusinessLogic:
    """비즈니스로직 카테고리 보안 검증 (ID 30~36)"""

    # -- ID 30 ---------------------------------------------------------------
    @allure.title("ID-30 권한 회수 후 이전 토큰 재접근 차단")
    @allure.label("tc_id", "30")
    @allure.label("priority", "P0")
    def test_id30_권한회수_후_이전토큰_차단(self, educator_client, withdraw_token):
        """전용 계정에 권한을 부여했다가 회수한 뒤, 회수 전 발급된 토큰으로
        재접근 시 즉시 차단되어야 함

        [기대] 403/404 또는 200+insufficient_permission
        200 + 정상 데이터면 권한 회수가 지연 반영되는 결함이다.

        [흐름] 등록(POST /member/bulk) → 재접근 가능 확인용 토큰 확보(이미 보유) →
        회수(DELETE /member/{id}) → 그 토큰으로 재접근 시도.
        SEC_WITHDRAW_ID 계정은 등록·회수를 반복해도 소모되지 않아 재실행 가능하다.
        """
        classroom = ClassroomApi(educator_client)
        account_id = token_utils.decode_payload(withdraw_token)["_id"]

        grant_response = classroom.add_members(CLASSROOM_ID, [account_id])
        assert_http(grant_response, 200)

        member_id = None
        for _ in range(5):
            members = json_body(classroom.list_members(CLASSROOM_ID))
            match = next((m for m in members if m.get("account_id") == account_id), None)
            if match:
                member_id = match["id"]
                break
            time.sleep(0.5)

        assert member_id, (
            f"{WITHDRAW_LOGIN_ID} 등록 후 구성원 목록에서 찾지 못함 - "
            "POST /member/bulk 응답은 200이었으나 반영 지연 가능성 있음"
        )

        revoke_response = classroom.delete_member(member_id, CLASSROOM_ID)
        assert_http(revoke_response, (200, 204))

        withdrawn_client = APIClient(token=withdraw_token, role="withdrawn-student")
        access_after = ClassroomApi(withdrawn_client).get_classroom(CLASSROOM_ID)

        assert_business_rejected(access_after, context="권한 회수 후 접근")

    # -- ID 31 ---------------------------------------------------------------
    @allure.title("ID-31 수강생의 역할변경(교육자 승격) 차단")
    @pytest.mark.skip(
        reason="Not Available: 구성원 관리 화면에 역할 변경 UI가 없고, "
        "HAR 분석 결과 역할변경 PATCH API 자체가 존재하지 않아 검증 대상 부재"
    )
    @allure.label("tc_id", "31")
    @allure.label("priority", "P2")
    def test_id31_수강생_역할변경_차단(self):
        """수강생이 스스로를 교육자로 승격할 수 없어야 함 (대상 API 부재로 검증 불가)"""

    # -- ID 32 ---------------------------------------------------------------
    @allure.title("ID-32 수강생의 타인 강제퇴장 차단")
    @allure.label("tc_id", "32")
    @allure.label("priority", "P0")
    def test_id32_수강생_타인_강제퇴장_차단(self, student_client):
        """학생 토큰으로 타 구성원 삭제(DELETE) 시도 시 차단되어야 함

        [기대] 403 + has_no_permission
        구성원 퇴출은 관리 권한이 필요한 기능이므로, 수강생이 호출하면 거부되어야 한다.
        200이면 권한 없는 사용자가 타인을 클래스에서 쫓아낼 수 있다는 뜻(인가 결함).
        """
        classroom = ClassroomApi(student_client)
        response = classroom.delete_member(OTHER_MEMBER_ID, CLASSROOM_ID)

        assert_business_rejected(response, context="수강생의 타인 강제퇴장")

    # -- ID 33 ---------------------------------------------------------------
    @allure.title("ID-33 타인 과제 제출물 접근 차단")
    @pytest.mark.skip(
        reason="Not Available: 클래스 내 과제(material_assignment) 콘텐츠가 없고 "
        "과목 생성 기능도 동작하지 않아 검증 대상 제출물(submission_id) 확보 불가"
    )
    @allure.label("tc_id", "33")
    @allure.label("priority", "P2")
    def test_id33_타인_제출물_접근_차단(self):
        """본인 제출물만 조회되어야 함 (검증 대상 리소스 부재로 검증 불가)"""

    # -- ID 34 ---------------------------------------------------------------
    @allure.title("ID-34 수강생의 성적 직접 수정 차단")
    @pytest.mark.skip(
        reason="Not Available: 교육자 화면에도 점수 수동 수정 UI가 없고 "
        "score/grade 관련 수정 API 호출이 확인되지 않아 대상 API 부재"
    )
    @allure.label("tc_id", "34")
    @allure.label("priority", "P2")
    def test_id34_수강생_성적_직접수정_차단(self):
        """수강생이 성적을 수정할 수 없어야 함 (대상 API 부재로 검증 불가)"""

    # -- ID 35 ---------------------------------------------------------------
    @allure.title("ID-35 시험 재응시 횟수제한 우회 차단")
    @pytest.mark.slow
    @allure.label("tc_id", "35")
    @allure.label("priority", "P1")
    def test_id35_시험_재응시_횟수제한(self, student_client):
        """시험 초기화 API를 반복 호출해 재응시 제한이 서버에서 강제되는지 검증

        [기대] 제한 횟수 초과 시 거부(_result.status=fail)
        [실제] 20회 전부 200 OK(status=ok) → 재응시 제한 없음 → FAIL(빨간불)

        제한이 없으면 학생이 틀린 문제를 확인한 뒤 초기화·재응시를 반복해
        만점을 만들 수 있는 부정행위 경로가 열린다.
        """
        lxp = LxpApi(student_client)

        success_count = 0
        rejected_at = None

        for attempt in range(1, RESET_ATTEMPT_COUNT + 1):
            response = lxp.reset_test_by_self(RESET_LECTURE_ID)

            if is_business_rejected(response):
                rejected_at = attempt
                break

            body = json_body(response)
            assert body.get("_result", {}).get("status") == "ok", (
                f"{attempt}회차 응답이 성공도 거부도 아님 - BODY={response.text[:500]}"
            )
            success_count += 1

        allure.attach(
            f"연속 성공 {success_count}회 / 거부 시점: {rejected_at or '없음'}",
            name="재응시 초기화 호출 결과",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert rejected_at is not None, (
            f"시험 초기화를 {success_count}회 연속 호출했으나 한 번도 거부되지 않음 - "
            "재응시 횟수 제한이 서버에 없어 응시 기간 내 무제한 재응시 가능(부정행위 경로)"
        )

    # -- ID 36 ---------------------------------------------------------------
    @allure.title("ID-36 시험 시간종료 후 제출 차단")
    @allure.label("tc_id", "36")
    @allure.label("priority", "P1")
    def test_id36_시험_시간종료후_제출_차단(self, student_client):
        """제한 시간이 종료된 시험에 답안 제출 시 서버가 거부해야 함

        [기대] 409 + fail_code=ready_test_admission_status
        시간이 끝나면 응시 상태가 해제되므로, 화면을 거치지 않고 제출 API를
        직접 호출해도 거부되어야 한다. 200이면 종료 후 제출로 부정행위가 가능하다.

        [사전조건] SEC_TIMEOUT_QUIZ_ID는 제한시간이 이미 종료된 시험의 문항이어야 한다.
        """
        lxp = LxpApi(student_client)
        response = lxp.add_quiz_response(TIMEOUT_QUIZ_ID, "test")

        assert_business_rejected(response, context="시험 종료 후 답안 제출")
