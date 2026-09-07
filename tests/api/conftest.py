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
from utils.auto_data import AutoDataResolver
from utils.tc_catalog import TC_META


ROOT_DIR = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# V19 result policy: Negative TC = actual pytest FAILED
# ---------------------------------------------------------------------------
# 프로젝트 표시 요구:
#
# - Positive TC 정상 동작       -> PASSED
# - Negative TC 기대 동작 확인 -> FAILED (EXPECTED NEGATIVE)
# - Negative TC 실제 이상      -> FAILED (UNEXPECTED NEGATIVE)
# - 사전조건 미충족            -> SKIPPED
#
# @pytest.mark.negative TC가 기능적으로 올바르게 차단되어도
# pytest의 실제 call outcome 자체를 FAILED로 변환한다.
# 따라서 터미널 / Allure / Jenkins 모두 Failed로 본다.

_NEGATIVE_NODEIDS = set()


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
    _NEGATIVE_NODEIDS.clear()

    # Negative TC 목록은 기존대로 유지
    for item in items:
        if item.get_closest_marker("negative") is not None:
            _NEGATIVE_NODEIDS.add(item.nodeid)

    # API 테스트만 실행하는 경우 TC01 -> TC68 순으로 정렬
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


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item, call):
    """
    정상적으로 검증을 끝낸 Negative TC도 프로젝트 정책상 actual FAILED로 변환한다.

    trylast hookwrapper를 사용해 Allure 같은 report 소비 플러그인이
    최종 FAILED outcome을 보도록 한다.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    if item.nodeid not in _NEGATIVE_NODEIDS:
        return

    if report.passed:
        report.outcome = "failed"
        report.longrepr = (
            "EXPECTED NEGATIVE RESULT\n"
            "이 TC는 API 실패/권한 차단/유효성 차단 등 Negative 결과를 검증합니다.\n"
            "기대된 Negative 동작이 확인되었으므로 프로젝트 표시 정책에 따라 "
            "pytest 결과를 FAILED로 기록합니다."
        )
        report.user_properties.append(("negative_result", "EXPECTED"))
        report.user_properties.append(("v19_forced_failed", "true"))
    elif report.failed:
        report.user_properties.append(("negative_result", "UNEXPECTED"))


def pytest_report_teststatus(report, config):
    if report.when != "call" or report.nodeid not in _NEGATIVE_NODEIDS:
        return None

    props = dict(getattr(report, "user_properties", []))

    if report.failed and props.get("negative_result") == "EXPECTED":
        return "failed", "F", "FAILED (EXPECTED NEGATIVE)"

    if report.failed:
        return "failed", "F", "FAILED (UNEXPECTED NEGATIVE)"

    return None


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    expected_negative = []
    unexpected_negative = []

    for report in terminalreporter.stats.get("failed", []):
        if report.when != "call" or report.nodeid not in _NEGATIVE_NODEIDS:
            continue

        props = dict(getattr(report, "user_properties", []))
        if props.get("negative_result") == "EXPECTED":
            expected_negative.append(report)
        else:
            unexpected_negative.append(report)

    terminalreporter.write_sep("-", "V19 Negative TC Result")
    terminalreporter.write_line(
        f"FAILED (EXPECTED NEGATIVE)   : {len(expected_negative)}"
    )
    terminalreporter.write_line(
        f"FAILED (UNEXPECTED NEGATIVE) : {len(unexpected_negative)}"
    )
    terminalreporter.write_line(
        "※ V19에서는 Negative TC를 실제 pytest FAILED로 집계하며 "
        "Allure/Jenkins에도 Failed로 전달합니다."
    )


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
    if not settings.STSESSION_B_KEY:
        pytest.skip(
            "TC60/TC61/TC67용 STSESSION_B_KEY이 설정되지 않았습니다."
        )
    client = APIClient(settings.STSESSION_B_KEY, role="student_b")
    yield client
    client.close()


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
