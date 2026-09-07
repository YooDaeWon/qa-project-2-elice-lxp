import shutil
from pathlib import Path

import pytest

from config.settings import load_local_dotenv
from framework.loadtest.accounts import load_accounts


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACCOUNT_CSV = Path(__file__).resolve().parent / "data" / "QA6test_account_list_(30).csv"
load_local_dotenv()


def pytest_configure(config):
    """이전 Allure history를 다음 실행 결과에 이어 붙인다"""
    alluredir = config.getoption("--alluredir", default=None)
    if not alluredir:
        return

    history_src = PROJECT_ROOT / "allure-report" / "history"
    if not history_src.exists():
        return

    history_dst = Path(alluredir) / "history"
    shutil.copytree(history_src, history_dst, dirs_exist_ok=True)


@pytest.fixture(scope="session")
def accounts():
    """CSV에서 부하 테스트 계정 읽기"""
    loaded = load_accounts(ACCOUNT_CSV)
    if not loaded:
        pytest.fail("🚨 CSV 파일에서 계정을 하나도 읽지 못했습니다.")
    return loaded
