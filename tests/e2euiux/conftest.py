import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from dotenv import load_dotenv
from playwright.sync_api import expect


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VIDEO_ROOT = PROJECT_ROOT / "videos"
LECTURE_IDS = ("1645", "1741")
load_dotenv(PROJECT_ROOT / ".env")
expect.set_options(timeout=30_000)


# E2E flow 실행 순서
E2E_FLOW_ORDER = (
    "exam_flow",
    "board_flow",
    "schedule_flow",
    "exam_retake_flow",
    "schedule_management_flow",
    "exam_status_flow",
    "exam_multi",
    "exam_reload_save",
    "board_offline",
    "board_duplicate",
    "board_title_limit",
    "exam_offline",
    "exam_timeout",
    "invalid_url",
    "responsive_layout",
    "mocking500",
    "login_flow",
)
_FLOW_ORDER = {
    flow_name: order
    for order, flow_name in enumerate(E2E_FLOW_ORDER)
}


def _is_e2e_test(item):
    """E2E 테스트 여부 확인"""
    nodeid = item.nodeid.replace("\\", "/")
    return nodeid.startswith("tests/e2euiux/") or "/tests/e2euiux/" in nodeid


def _get_flow_name(item):
    """테스트에 지정된 flow marker 확인"""
    for marker in item.iter_markers():
        if marker.name in _FLOW_ORDER:
            return marker.name
    return None


def _get_tc_id(item):
    """Allure tc_id 확인"""
    for marker in item.iter_markers(name="allure_label"):
        if marker.kwargs.get("label_type") != "tc_id":
            continue
        if marker.args and str(marker.args[0]).isdigit():
            return int(marker.args[0])
    return None


def _get_allure_full_name(item):
    """테스트 항목의 Allure fullName 생성"""
    nodeid = item.nodeid.replace("\\", "/")
    test_path, *test_parts = nodeid.split("::")
    module_name = test_path[:-3].replace("/", ".")
    test_parts = [part.split("[", 1)[0] for part in test_parts]
    test_name = test_parts[-1]
    class_name = ".".join(test_parts[:-1])

    if class_name:
        return f"{module_name}.{class_name}#{test_name}"
    return f"{module_name}#{test_name}"


def pytest_collection_modifyitems(items):
    """E2E flow와 TC ID 기준으로 수집 순서 고정"""
    e2e_items = []

    for original_index, item in enumerate(items):
        if not _is_e2e_test(item):
            continue

        flow_name = _get_flow_name(item)
        tc_id = _get_tc_id(item)
        if flow_name is None or tc_id is None:
            raise pytest.UsageError(
                "E2E 테스트에 flow marker 또는 Allure tc_id가 없습니다: "
                f"{item.nodeid}"
            )

        e2e_items.append(
            (
                _FLOW_ORDER[flow_name],
                tc_id,
                original_index,
                item,
            )
        )

    if not e2e_items:
        return

    e2e_items.sort(key=lambda row: row[:3])
    ordered_e2e_items = iter(row[3] for row in e2e_items)
    items[:] = [
        next(ordered_e2e_items) if _is_e2e_test(item) else item
        for item in items
    ]


def _reset_lectures(e2e_page, lecture_ids):
    """지정한 시험 재응시 허용"""
    api_base_url = os.getenv("API_BASE_URL")
    org = os.getenv("ORG")
    session_key = os.getenv("TCSESSION_KEY")

    if not all((api_base_url, org, session_key)):
        pytest.fail(".env에 API 설정값을 입력하세요")

    for lecture_id in lecture_ids:
        response = e2e_page.request.post(
            f"{api_base_url.rstrip('/')}/org/{org}/lecture/test/reset/",
            headers={"Authorization": f"Bearer {session_key}"},
            multipart={"lecture_id": lecture_id},
        )

        assert response.ok, f"{lecture_id} 재응시 허용 API 호출 실패"
        assert response.json().get("_result", {}).get("status") == "ok", (
            f"{lecture_id} 재응시 허용 API 처리 실패"
        )


@pytest.fixture(scope="session")
def credentials():
    """환경변수에서 학습자 로그인 정보 읽기"""
    return {
        "user_id": os.environ["ST_ID"],
        "password": os.environ["ST_PW"],
    }


@pytest.fixture(scope="session")
def educator_credentials():
    """환경변수에서 교육자 로그인 정보 읽기"""
    return {
        "user_id": os.environ["TC_ID"],
        "password": os.environ["TC_PW"],
    }


def _flow_video_directory(config, flow_name):
    """흐름별 임시 영상 저장 경로"""
    video_dirs = getattr(config, "_flow_video_dirs", None)
    if video_dirs is None:
        video_dirs = {}
        config._flow_video_dirs = video_dirs

    if flow_name not in video_dirs:
        video_dirs[flow_name] = Path(
            tempfile.mkdtemp(prefix=f"{flow_name}-")
        )

    return video_dirs[flow_name]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """실패한 테스트의 흐름 기록"""
    outcome = yield
    report = outcome.get_result()

    if not report.failed:
        return

    module = getattr(item, "module", None)
    flow_name = getattr(module, "__name__", None)
    if flow_name is None:
        return

    failed_flows = getattr(item.config, "_failed_flow_names", None)
    if failed_flows is None:
        failed_flows = set()
        item.config._failed_flow_names = failed_flows

    failed_flows.add(flow_name)

    failed_tests = getattr(item.config, "_failed_allure_tests", None)
    if failed_tests is None:
        failed_tests = {}
        item.config._failed_allure_tests = failed_tests

    failed_tests.setdefault(flow_name, {"names": set(), "tc_ids": set()})
    failed_tests[flow_name]["names"].add(_get_allure_full_name(item))

    tc_id = _get_tc_id(item)
    if tc_id is not None:
        failed_tests[flow_name]["tc_ids"].add(str(tc_id))


def _get_allure_results_directory(config):
    """Allure 결과 저장 경로 확인"""
    allure_dir = getattr(config.option, "allure_report_dir", None)
    if not allure_dir:
        return None
    return Path(allure_dir).resolve()


def _result_belongs_to_flow(result, flow_name):
    """Allure 결과와 E2E 흐름 일치 여부 확인"""
    result_full_name = result.get("fullName", "")
    result_module = result_full_name.split("#", 1)[0]
    return (
        result_module == flow_name
        or result_module.endswith(f".{flow_name}")
    )


def _result_has_tc_id(result, tc_ids):
    """Allure 결과의 tc_id 일치 여부 확인"""
    for label in result.get("labels", []):
        if label.get("name") == "tc_id" and str(label.get("value")) in tc_ids:
            return True
    return False


def _attach_flow_videos_to_allure(config, preserved_videos):
    """실패한 E2E 흐름 영상을 Allure 결과에 첨부"""
    allure_dir = _get_allure_results_directory(config)
    failed_tests = getattr(config, "_failed_allure_tests", {})

    if not allure_dir or not allure_dir.is_dir() or not failed_tests:
        return

    for result_path in allure_dir.glob("*-result.json"):
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        if result.get("status") not in ("failed", "broken"):
            continue

        for flow_name, video_paths in preserved_videos.items():
            failed_test_info = failed_tests.get(flow_name)
            if not failed_test_info:
                continue

            full_name_matches = (
                result.get("fullName") in failed_test_info["names"]
            )
            tc_id_matches = (
                _result_has_tc_id(result, failed_test_info["tc_ids"])
                and _result_belongs_to_flow(result, flow_name)
            )
            if not (full_name_matches or tc_id_matches):
                continue

            attachments = result.get("attachments") or []
            result["attachments"] = attachments
            for video_path in video_paths:
                source_name = f"{result_path.stem}-{video_path.name}"
                allure_video_path = allure_dir / source_name

                if not allure_video_path.exists():
                    try:
                        shutil.copy2(video_path, allure_video_path)
                    except OSError:
                        continue

                if any(
                    attachment.get("source") == source_name
                    for attachment in attachments
                ):
                    continue

                attachments.append(
                    {
                        "name": f"Playwright video - {flow_name}",
                        "source": source_name,
                        "type": "video/webm",
                    }
                )

            try:
                result_path.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except OSError:
                continue


def pytest_sessionfinish(session, exitstatus):
    """흐름별 영상을 사용자 폴더로 이동"""
    config = session.config
    video_option = config.getoption("--video")
    video_dirs = getattr(config, "_flow_video_dirs", {})
    failed_flows = getattr(config, "_failed_flow_names", set())

    preserved_videos = {}

    for flow_name, temp_dir in video_dirs.items():
        preserve_video = video_option == "on" or (
            video_option == "retain-on-failure"
            and flow_name in failed_flows
        )

        if preserve_video:
            target_dir = VIDEO_ROOT / flow_name
            target_dir.mkdir(parents=True, exist_ok=True)

            preserved_videos[flow_name] = []

            for video_path in temp_dir.glob("*.webm"):
                target_path = target_dir / video_path.name
                shutil.move(
                    str(video_path),
                    str(target_path),
                )
                preserved_videos[flow_name].append(target_path)

        shutil.rmtree(temp_dir, ignore_errors=True)

    _attach_flow_videos_to_allure(config, preserved_videos)


@pytest.fixture(scope="module")
def flow_browser_context_args(request, browser_context_args):
    """흐름별 브라우저 영상 설정"""
    context_args = browser_context_args.copy()
    context_args["locale"] = "ko-KR"

    video_option = request.config.getoption("--video")
    if video_option in ("on", "retain-on-failure"):
        flow_name = request.module.__name__
        context_args["record_video_dir"] = str(
            _flow_video_directory(request.config, flow_name)
        )

    return context_args


@pytest.fixture(scope="module")
def e2e_page(browser, flow_browser_context_args):
    """E2E 브라우저 상태 공유"""
    context = browser.new_context(**flow_browser_context_args)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def reset_exam(e2e_page):
    """시험 재응시 허용"""
    _reset_lectures(e2e_page, LECTURE_IDS)


@pytest.fixture(scope="module")
def reset_e2e01(e2e_page):
    """e2e-01 시험 재응시 허용"""
    _reset_lectures(e2e_page, ("1645",))


@pytest.fixture
def reset_timeout(e2e_page):
    """timeout 시험 재응시 허용"""
    _reset_lectures(e2e_page, ("1741",))
