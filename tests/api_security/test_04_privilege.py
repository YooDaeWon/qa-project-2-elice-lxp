"""권한상승 보안 테스트 (ID 22~24)

대상: classroom-api
검증 방식: TC의 '기대 결과' 기준. 권한 밖 조작이 통하면 실패(빨간불)로 노출.

권한상승 = 일반 사용자가 자신의 권한을 넘어서는 작업을 수행하는 것.
- Mass Assignment: 요청 body에 권한 밖 필드(owner_id 등)를 끼워넣어 무단 변경
- Method Override: X-HTTP-Method-Override 헤더로 실제 메서드를 바꿔 권한 검사 우회
"""

import allure
import pytest

from config.settings import settings
from framework.api_security.pages.classroom_api import ClassroomApi
from utils.assertions import (
    assert_business_rejected,
    is_business_rejected,
    json_body,
)
from tests.api_security.conftest import MY_ACCOUNT_ID


CLASSROOM_ID = settings.CLASSROOM_ID


@allure.epic("API 호출 보안성 테스트")
@allure.feature("권한상승")
@allure.label("owner", "yoodaewon")
@allure.label("team", "QA4")
@pytest.mark.sec_privilege
class TestPrivilegeEscalation:
    """권한상승 카테고리 보안 검증 (ID 22~24)"""

    # -- ID 22 ---------------------------------------------------------------
    @allure.title("ID-22 권한 밖 필드 주입(Mass Assignment) 차단")
    @allure.label("tc_id", "22")
    def test_id22_권한밖_필드주입_차단(self, student_client):
        """학생 토큰으로 owner_id/organization_id를 주입해도 무시되어야 함

        검증 2단계:
        1) PATCH로 권한 밖 필드 주입 → 차단(403/422 또는 200+fail_code)되어야 함
        2) GET 재조회 → 주입한 값이 실제로 반영되지 않았는지 확인
        차단됐거나, 설령 통과 응답이어도 주입값이 반영 안 됐으면 안전(통과).
        """
        classroom = ClassroomApi(student_client)
        injected_org_id = 999999  # 원본과 확실히 다른 주입 시도값
        injection = {
            "name": "mass_assign_test",
            "owner_id": int(MY_ACCOUNT_ID),
            "organization_id": injected_org_id,
        }

        # 1) 주입 시도
        patch_response = classroom.patch_classroom(CLASSROOM_ID, injection)
        rejected = is_business_rejected(patch_response)

        # 2) 재조회하여 주입값 반영 여부 확인
        current = json_body(classroom.get_classroom(CLASSROOM_ID))
        org_reflected = current.get("organization_id") == injected_org_id

        # 안전 조건: 요청이 차단됐거나, (통과했어도) 주입값이 반영되지 않았어야 함
        assert rejected or not org_reflected, (
            "권한 밖 필드(organization_id) 주입이 실제로 반영됨 - "
            "Mass Assignment 취약점(일반 사용자가 기관/소유자를 무단 변경 가능)"
        )

    # -- ID 23 ---------------------------------------------------------------
    @allure.title("ID-23 구성원 역할 변경 주입 차단")
    @pytest.mark.skip(
        reason="구성원 역할 변경 기능 미구현 - 대상 API 부재로 검증 불가(N/A)"
    )
    @allure.label("tc_id", "23")
    def test_id23_구성원_역할변경_주입_차단(self):
        """구성원 역할 변경 API가 존재하지 않아 검증 대상이 없음 (N/A)

        classroom·LXP 명세에 role 쓰기 API가 없고, 관리 UI에도 역할 변경 기능이 없다.
        대상 엔드포인트가 생기면 이 테스트를 활성화하여 role/member_role 주입을 검증한다.
        """

    # -- ID 24 ---------------------------------------------------------------
    @allure.title("ID-24 요청방식(Method) 변조 우회 호출 차단")
    @allure.label("tc_id", "24")
    def test_id24_method_override_우회_차단(self, student_client):
        """POST에 X-HTTP-Method-Override:PATCH를 실어도 무시되어야 함 (403/405)

        [기대] override 헤더 무시 → 차단
        헤더 조작으로 POST를 PATCH로 바꿔 권한 검사를 우회할 수 없어야 한다.
        """
        classroom = ClassroomApi(student_client)
        response = classroom.post_with_method_override(
            CLASSROOM_ID, "PATCH", {"name": "override_test"}
        )

        assert_business_rejected(
            response, context="X-HTTP-Method-Override 우회 시도"
        )
