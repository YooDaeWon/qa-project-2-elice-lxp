import os
from pathlib import Path

import pytest
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LECTURE_IDS = ("1645", "1741")
load_dotenv(PROJECT_ROOT / ".env")


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


@pytest.fixture(scope="module")
def e2e_page(browser, browser_context_args):
    """E2E 브라우저 상태 공유"""
    context = browser.new_context(**browser_context_args)
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
