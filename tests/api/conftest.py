import json
from pathlib import Path

import re

import pytest

try:
    import allure
except ImportError:
    allure = None

from clients.api_client import APIClient
from config.settings import settings
from framework.api_security.pages.account_client import AccountClient
from utils.auto_data import AutoDataResolver
from utils.tc_catalog import TC_META


ROOT_DIR = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# API result policy
# ---------------------------------------------------------------------------
# pytest의 기본 결과 정책을 그대로 사용한다.
#
# - 기대결과와 실제결과가 일치하면: PASSED
# - 기대결과와 실제결과가 불일치하면: FAILED
# - 사전조건이 충족되지 않으면: SKIPPED
#
# @pytest.mark.negative는 네거티브 테스트를 분류하기 위한 메타데이터일 뿐,
# 테스트 결과(PASS/FAIL)를 강제로 변경하지 않는다. 따라서 Allure/Jenkins에도
# pytest의 실제 검증 결과가 그대로 전달된다.


def _is_api_test(item):
    nodeid = item.nodeid.replace("\\", "/")
    return nodeid.startswith("tests/api/") or "/tests/api/" in nodeid


def _api_tc_number(item):
    """통합된 카테고리 파일에서도 test_api_01 ~ test_api_68의 TC 번호를 반환한다."""
    match = re.fullmatch(r"test_api_(\d{2})", item.name, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def pytest_collection_modifyitems(config, items):
    """API 테스트를 TC01 -> TC68 순으로 정렬한다."""
    numbered_items = []
    unnumbered_items = []

    for original_index, item in enumerate(items):
        tc_number = _api_tc_number(item)
        if tc_number is None:
            unnumbered_items.append((original_index, item))
        else:
            numbered_items.append((tc_number, original_index, item))

    numbered_items.sort(key=lambda row: (row[0], row[1]))

    if unnumbered_items:
        # 다른 테스트가 같이 수집된 경우 기존 항목은 유지하고 API TC를 번호순으로 배치
        items[:] = [item for _, item in unnumbered_items] + [
            item for _, _, item in numbered_items
        ]
    else:
        items[:] = [item for _, _, item in numbered_items]


@pytest.fixture(scope="session")
def student_client():
    if not settings.STSESSION_KEY:
        pytest.skip("STSESSION_KEY가 설정되지 않았습니다.")
    client = APIClient(settings.STSESSION_KEY, role="student")
    yield client
    client.close()


@pytest.fixture(scope="session")
def educator_client():
    if not settings.TCSESSION_KEY:
        pytest.skip("TCSESSION_KEY가 설정되지 않았습니다.")
    client = APIClient(settings.TCSESSION_KEY, role="educator")
    yield client
    client.close()


@pytest.fixture(scope="session")
def student_a_client():
    token = settings.STSESSION_A_KEY or settings.STSESSION_KEY
    if not token:
        pytest.skip("STSESSION_KEY가 설정되지 않았습니다.")
    client = APIClient(token, role="student_a")
    yield client
    client.close()


@pytest.fixture(scope="session")
def student_b_client():
    """기존 STSESSION_B_KEY 기반 수강생 B 클라이언트.

    다른 테스트에서 계속 사용할 수 있도록 기존 동작을 유지한다.
    """
    if not settings.STSESSION_B_KEY:
        pytest.skip("STSESSION_B_KEY가 설정되지 않았습니다.")
    client = APIClient(settings.STSESSION_B_KEY, role="student_b")
    yield client
    client.close()


@pytest.fixture(scope="function")
def dummy_2_client():
    """TC60/TC61/TC67 전용 더미계정으로 테스트마다 새 토큰을 발급한다."""
    login_id = settings.DUMMY_2_ID
    password = settings.DUMMY_2_PW

    if not login_id or not password:
        pytest.skip(
            "TC60/TC61/TC67 전용 더미계정이 설정되지 않았습니다. "
            ".env에 DUMMY_2_ID와 DUMMY_2_PW를 입력하세요."
        )

    account_client = AccountClient()
    try:
        response = account_client.login(login_id, password)

        try:
            data = response.json()
        except ValueError:
            data = {}

        token = data.get("access_token") if isinstance(data, dict) else None

        if response.status_code != 200 or not token:
            fail_code = data.get("fail_code") if isinstance(data, dict) else None
            fail_message = data.get("fail_message") if isinstance(data, dict) else None
            pytest.fail(
                "DUMMY_2 로그인 또는 access_token 발급 실패 | "
                f"http={response.status_code}, "
                f"fail_code={fail_code}, fail_message={fail_message}"
            )

        print("[DUMMY_2 AUTH] 로그인 성공 - 이번 테스트용 새 access_token 발급 완료")

        client = APIClient(token, role="dummy_2_student")
        try:
            yield client
        finally:
            client.close()
    finally:
        account_client.api.close()


@pytest.fixture(scope="session")
def payloads():
    result = {}

    for group in ("classroom", "course", "schedule", "board"):
        path = ROOT_DIR / "data" / "payloads" / f"{group}.json"
        with path.open("r", encoding="utf-8") as f:
            result[group] = json.load(f)

    return result


@pytest.fixture(scope="session", autouse=True)
def auto_discover_test_data(student_client, educator_client):
    """pytest 실행 시 필요한 ID를 자동 조회/생성한다."""
    if not settings.AUTO_DISCOVER:
        yield
        return

    student_b_api = (
        APIClient(settings.STSESSION_B_KEY, role="student_b_auto")
        if settings.STSESSION_B_KEY
        else None
    )

    resolver = AutoDataResolver(
        educator_api=educator_client,
        student_api=student_client,
        student_b_api=student_b_api,
    )

    # 자동 fixture 준비 요청 수십 건이 첫 TC의 Allure Step에 섞이지 않도록 숨긴다.
    traced_clients = [educator_client, student_client]
    if student_b_api:
        traced_clients.append(student_b_api)
    for api in traced_clients:
        api.trace_allure = False

    resolver.discover_all()

    for api in traced_clients:
        api.trace_allure = True

    yield resolver

    for api in traced_clients:
        api.trace_allure = False
    if settings.AUTO_SETUP_TEST_DATA:
        resolver.cleanup()

    if student_b_api:
        student_b_api.close()


@pytest.fixture(autouse=True)
def allure_tc_metadata(request):
    """API TC 번호/기대결과를 Allure에 붙여 테스트케이스와 실행 증거를 추적한다."""
    if not _is_api_test(request.node):
        yield
        return

    if allure is None:
        yield
        return

    name = request.node.name
    tc_id = None
    # 분리 전 함수명: test_tc01_...
    match_old = re.search(r"test_tc(\\d{2})", name, re.IGNORECASE)
    if match_old:
        tc_id = f"TC{match_old.group(1)}"

    # 분리 후 함수명: test_api_01
    if tc_id is None:
        match_new = re.fullmatch(r"test_api_(\\d{2})", name, re.IGNORECASE)
        if match_new:
            tc_id = f"TC{match_new.group(1)}"

    meta = TC_META.get(tc_id)
    if meta:
        title, feature, expected = meta
        allure.dynamic.epic("Elice LXP QA Final Project")
        allure.dynamic.feature(feature)
        allure.dynamic.story(tc_id)
        allure.dynamic.title(f"{tc_id} | {title}")

        markers = {marker.name for marker in request.node.iter_markers()}
        tc_type = "Negative" if "negative" in markers else "Positive"
        if "destructive" in markers:
            tc_type += " / Destructive"
        allure.dynamic.tag(tc_type)
        if "manual_ui_check" in markers:
            allure.dynamic.tag("Manual UI Check Required")

        allure.dynamic.description(
            f"TC: {tc_id}\n분류: {feature}\n유형: {tc_type}\n\nExpected Result:\n{expected}"
        )
        allure.attach(
            expected,
            name="Expected Result",
            attachment_type=allure.attachment_type.TEXT,
        )

    yield
