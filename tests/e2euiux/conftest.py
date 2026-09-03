import os
import shutil
import tempfile
from pathlib import Path

import pytest
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VIDEO_ROOT = PROJECT_ROOT / "videos"
LECTURE_IDS = ("1645", "1741")
load_dotenv(PROJECT_ROOT / ".env")


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
    org_name = os.getenv("ORG_NAME")
    session_key = os.getenv("TCSESSION_KEY")

    if not all((api_base_url, org_name, session_key)):
        pytest.fail(".env에 API 설정값을 입력하세요")

    for lecture_id in lecture_ids:
        response = e2e_page.request.post(
            f"{api_base_url.rstrip('/')}/org/{org_name}/lecture/test/reset/",
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


def pytest_sessionfinish(session, exitstatus):
    """흐름별 영상을 사용자 폴더로 이동"""
    config = session.config
    video_option = config.getoption("--video")
    video_dirs = getattr(config, "_flow_video_dirs", {})
    failed_flows = getattr(config, "_failed_flow_names", set())

    for flow_name, temp_dir in video_dirs.items():
        preserve_video = video_option == "on" or (
            video_option == "retain-on-failure"
            and flow_name in failed_flows
        )

        if preserve_video:
            target_dir = VIDEO_ROOT / flow_name
            target_dir.mkdir(parents=True, exist_ok=True)

            for video_path in temp_dir.glob("*.webm"):
                shutil.move(
                    str(video_path),
                    str(target_dir / video_path.name),
                )

        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def flow_browser_context_args(request, browser_context_args):
    """흐름별 브라우저 영상 설정"""
    context_args = browser_context_args.copy()

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
