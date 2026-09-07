"""정보노출(웹 취약점) 보안 테스트 (ID 43~47)

대상: LXP(dev-qatrack-api), classroom-api, dashboard-api
검증 방식: TC의 '기대 결과' 기준. 필요 이상의 정보가 밖으로 나가면 실패(빨간불).

정보노출 계열 보안 이슈:
- 과다노출: 기능에 불필요한 민감 필드가 응답에 실리면 공격 표면이 넓어진다
- 조회량 제한: 상한이 없으면 대량 수집·서버 부하로 이어진다
- 오류 응답: 스택트레이스·내부 경로가 공격자에게 힌트를 준다
- 캐시 제어: 민감 응답에 저장 금지 지시가 없으면 공용 PC·프록시에 남는다
- 그림자 API: 명세에 없는 엔드포인트도 동일한 인증·인가를 받아야 한다
"""

from pathlib import Path

import allure
import pytest

from config.settings import settings
from framework.api_security.pages.classroom_api import ClassroomApi
from framework.api_security.pages.dashboard_api import DashboardApi
from framework.api_security.pages.lxp_api import LxpApi
from framework.api_security.spec_diff import find_shadow_apis, format_shadow_report
from utils.assertions import is_business_rejected, json_body


CLASSROOM_ID = settings.CLASSROOM_ID
COURSE_ID = settings.COURSE_ID
MY_STUDENT_ID = settings.STUDENT_ID
OTHER_STUDENT_ID = settings.OTHER_STUDENT_ID

# ID-47 대조에 쓰는 데이터 파일 (프로젝트 루트 기준 data/)
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SPEC_FILES = {
    "dev-qatrack-api.dev.elicer.io": DATA_DIR / "lxp_api_spec_lecture.html",
    "dev-qatrack-classroom-api.dev.elicer.io": DATA_DIR / "lxp_api_spec_classroom.html",
}
HAR_SUMMARY_PATH = DATA_DIR / "har_summary.json"

# 응답에 실리면 안 되는 민감 필드명 (부분 일치로 검사)
SENSITIVE_FIELD_KEYWORDS = (
    "password",
    "passwd",
    "pw_hash",
    "call_code",
    "secret",
    "session_key",
    "sessionkey",
    "access_token",
    "refresh_token",
    "private_key",
)

# 오류 응답에 노출되면 안 되는 내부 정보 키워드
INTERNAL_LEAK_KEYWORDS = (
    "traceback",
    "file \"/",
    "line 1",
    "psycopg",
    "sqlalchemy",
    "postgres",
    "site-packages",
    "/usr/local",
    "/home/",
)

# 과도한 조회량 요청값 (서버가 상한으로 제한해야 함)
EXCESSIVE_COUNT = 100000

# 상한이 적용됐다고 인정할 최대 반환 건수
REASONABLE_MAX_ITEMS = 100

# 형식이 잘못된 UUID (파싱 오류 유발용)
MALFORMED_UUID = "not-a-valid-uuid"

# 민감 응답에 있어야 할 캐시 방지 헤더
CACHE_CONTROL_HEADERS = ("Cache-Control", "Pragma", "Expires")


def _collect_sensitive_fields(data, found=None, path=""):
    """응답 구조를 재귀 순회하며 민감 필드명을 수집"""
    if found is None:
        found = []

    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower()
            current = f"{path}.{key}" if path else str(key)
            if any(word in key_lower for word in SENSITIVE_FIELD_KEYWORDS):
                found.append(current)
            _collect_sensitive_fields(value, found, current)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            _collect_sensitive_fields(item, found, f"{path}[{index}]")

    return found


def _count_items(data):
    """응답에서 목록 길이를 추출 (구조가 달라도 가장 긴 리스트를 기준으로 함)"""
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        lengths = [
            len(value) for value in data.values() if isinstance(value, list)
        ]
        return max(lengths) if lengths else 0
    return 0


@allure.epic("API 호출 보안성 테스트")
@allure.feature("정보노출(웹 취약점)")
@allure.label("owner", "yoodaewon")
@allure.label("team", "QA4")
@pytest.mark.sec_info_disclosure
class TestInfoDisclosure:
    """정보노출 카테고리 보안 검증 (ID 43~47)"""

    # -- ID 43 ---------------------------------------------------------------
    @allure.title("ID-43 응답 내 민감정보 과다노출 차단")
    @allure.label("tc_id", "43")
    def test_id43_민감정보_과다노출_차단(self, student_client):
        """본인 프로필 응답에 기능상 불필요한 민감 필드가 실리는지 확인

        [기대] 비밀번호 해시·내부토큰·call_code·타인정보 미포함
        프로필 조회에 필요 없는 값이 함께 내려오면 그만큼 공격 표면이 넓어진다.
        """
        lxp = LxpApi(student_client)
        response = lxp.get_user()

        data = json_body(response)
        leaked_fields = _collect_sensitive_fields(data)

        allure.attach(
            f"검사한 민감 키워드={SENSITIVE_FIELD_KEYWORDS}\n"
            f"발견된 필드={leaked_fields or '없음'}\n"
            f"응답 일부={response.text[:800]}",
            name="프로필 응답 민감 필드 점검",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert not leaked_fields, (
            f"프로필 응답에 민감 필드가 포함됨: {leaked_fields} - "
            "기능상 불필요한 값까지 노출되어 공격 표면이 넓어짐"
        )

    # -- ID 44 ---------------------------------------------------------------
    @allure.title("ID-44 과도한 조회량 요청 제한")
    @allure.label("tc_id", "44")
    def test_id44_과도한_조회량_제한(self, student_client):
        """목록 API에 비정상적으로 큰 count를 요청해 서버가 제한하는지 확인

        [기대] 서버 최대치로 제한하거나 거부
        상한이 없으면 한 번의 요청으로 대량 수집이 가능하고 서버 부하로도 이어진다.
        거부(4xx)든 상한 적용이든 '무제한 반환만 아니면' 정상으로 본다.
        """
        classroom = ClassroomApi(student_client)
        response = classroom.get_articles(CLASSROOM_ID, skip=0, count=EXCESSIVE_COUNT)

        if is_business_rejected(response):
            allure.attach(
                f"요청 count={EXCESSIVE_COUNT} / 응답={response.status_code} (거부)\n"
                f"BODY={response.text[:500]}",
                name="과도한 조회량 요청 결과",
                attachment_type=allure.attachment_type.TEXT,
            )
            return

        item_count = _count_items(json_body(response))
        allure.attach(
            f"요청 count={EXCESSIVE_COUNT} / 응답={response.status_code} / 반환 건수={item_count}",
            name="과도한 조회량 요청 결과",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert item_count <= REASONABLE_MAX_ITEMS, (
            f"count={EXCESSIVE_COUNT} 요청에 {item_count}건이 그대로 반환됨 - "
            "조회량 상한이 없어 대량 수집·서버 부하 위험"
        )

    # -- ID 45 ---------------------------------------------------------------
    @allure.title("ID-45 오류 응답 내부정보 노출 차단")
    @allure.label("tc_id", "45")
    def test_id45_오류응답_내부정보_노출_차단(self, student_client):
        """형식이 잘못된 UUID로 조회해 오류 응답에 내부 정보가 담기는지 확인

        [기대] 스택트레이스·내부경로·서버버전·DB구조 미노출
        오류 메시지는 무엇이 잘못됐는지만 알려야 하며,
        시스템 구조를 알려주면 공격자에게 힌트가 된다.
        """
        classroom = ClassroomApi(student_client)
        response = classroom.get_classroom(MALFORMED_UUID)

        assert is_business_rejected(response), (
            f"잘못된 형식의 UUID 요청이 거부되지 않음 (status={response.status_code})"
        )

        body_lower = response.text.lower()
        leaked = [word for word in INTERNAL_LEAK_KEYWORDS if word in body_lower]

        allure.attach(
            f"요청 UUID={MALFORMED_UUID}\n응답={response.status_code}\n"
            f"발견된 내부정보={leaked or '없음'}\nBODY={response.text[:800]}",
            name="오류 응답 점검",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert not leaked, (
            f"오류 응답에 내부 정보가 노출됨: {leaked} - "
            f"BODY={response.text[:500]}"
        )

    # -- ID 46 ---------------------------------------------------------------
    @allure.title("ID-46 민감정보 응답의 캐시 제어 헤더 설정")
    @allure.label("tc_id", "46")
    def test_id46_민감응답_캐시방지_헤더(self, student_client):
        """개인 성적·학습정보 응답에 캐시 방지 헤더가 설정됐는지 확인

        [기대] Cache-Control: no-store(또는 no-cache, private) 등 존재
        [실제] Cache-Control·Pragma·Expires 3종 모두 없음 → FAIL(빨간불)

        저장 금지 지시가 없으면 브라우저나 중간 프록시가 응답을 보관할 수 있어,
        공용 PC에서 뒤로가기만 해도 이전 사용자의 성적이 보일 수 있다.
        """
        dashboard = DashboardApi(student_client)
        response = dashboard.get_student(MY_STUDENT_ID, CLASSROOM_ID, COURSE_ID)

        present = {
            name: response.headers.get(name)
            for name in CACHE_CONTROL_HEADERS
            if response.headers.get(name)
        }

        allure.attach(
            f"응답={response.status_code}\n"
            f"캐시 관련 헤더={present or '없음(3종 모두 부재)'}",
            name="캐시 제어 헤더 점검",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert present, (
            "개인 성적·학습정보 응답에 캐시 방지 헤더(Cache-Control/Pragma/Expires)가 "
            "하나도 없음 - 브라우저·프록시가 응답을 저장해 공용 PC에서 "
            "다음 사용자에게 이전 사용자의 정보가 노출될 수 있음"
        )

    # -- ID 47 ---------------------------------------------------------------
    @allure.title("ID-47 명세 미등록 API의 접근 통제")
    @allure.label("tc_id", "47")
    def test_id47_그림자API_접근통제(self, student_client):
        """명세에 없는 그림자 API가 타인 데이터를 차단하는지 확인

        [검증 절차]
        1) 제공된 기능 명세 2종(강의실·자료 386개 / 클래스 42개) 전체를 파싱
        2) 실제 호출 내역(HAR 요약본) 전체와 대조해 명세 미기재 호출을 식별
        3) 발견된 그림자 API 중 대표 케이스의 접근 통제를 실제 호출로 점검

        [기대] 명세에 없어도 인증·인가가 동일하게 적용되어 타인 데이터 차단
        [실제] 학생 토큰으로 타인 id 조회 시 200 + 타인 개인정보 반환 → FAIL(빨간불)

        문서에 없다고 보호가 면제되지는 않으며, 오히려 관리 대상에서 빠져
        권한 검사가 누락된 채 열려 있었다. 무인증 요청은 차단되므로
        '로그인 여부'는 보지만 '누구의 데이터인지'는 보지 않는다.
        """
        # 1~2단계: 명세 ↔ 실제 호출 대조
        diff_result = find_shadow_apis(SPEC_FILES, HAR_SUMMARY_PATH)

        allure.attach(
            format_shadow_report(diff_result),
            name="명세 ↔ 실제 호출 대조 결과",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert diff_result["shadow_hosts"] or diff_result["shadow_paths"], (
            "대조 결과가 비어 있음 - 명세 파일 또는 HAR 요약본을 확인해야 함"
        )

        # 3단계: 대표 그림자 API(dashboard-api)의 타인 데이터 접근 통제 점검
        dashboard = DashboardApi(student_client)
        response = dashboard.get_student(OTHER_STUDENT_ID, CLASSROOM_ID, COURSE_ID)

        allure.attach(
            f"대상=dashboard-api GET /student/{OTHER_STUDENT_ID} (명세 미기재 호스트)\n"
            f"조회 주체=학생 토큰 / 조회 대상=타인 id\n"
            f"응답={response.status_code}\nBODY={response.text[:800]}",
            name="그림자 API 타인 데이터 조회 결과",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert is_business_rejected(response), (
            f"명세 미등록 API에서 타인 id({OTHER_STUDENT_ID}) 데이터가 반환됨 "
            f"(status={response.status_code}) - 그림자 API에 인가 검사가 없어 "
            "정식 API의 차단을 우회하는 통로가 됨(IDOR). "
            f"대조 결과: 호스트 단위 {len(diff_result['shadow_hosts'])}개, "
            f"경로 단위 {len(diff_result['shadow_paths'])}건 발견"
        )
