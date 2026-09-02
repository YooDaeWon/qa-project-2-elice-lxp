import requests
import time
import concurrent.futures
import csv
import pytest
from pathlib import Path


# API 엔드포인트 정의
LOGIN_URL = "https://dev-qatrack-api.dev.elicer.io/global/auth/login/"
COURSE_URL = "https://dev-qatrack-api.dev.elicer.io/acl/course/get/"
TEST_ENTER_URL = "https://dev-qatrack-api.dev.elicer.io/org/{org}/lecture/test/enter/"
TEST_STOP_URL = (
    "https://dev-qatrack-api.dev.elicer.io/org/{org}/lecture/test/reset/by_self/"
)
TEST_RESET_URL = "https://dev-qatrack-api.dev.elicer.io/org/{org}/lecture/test/reset/"


# 현재 test_case08~11.py가 있는 Load_Test 폴더 기준 CSV 경로
BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "QA6test_account_list_(30).csv"


def load_accounts_from_csv(file_path=CSV_FILE):
    accounts = []

    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            accounts.append(row)

    return accounts


def execute_single_user_flow(my_account):
    """단일 유저가 1~4단계를 1회 완주하는 함수"""

    my_id = my_account.get("login_id")
    my_pw = my_account.get("password")

    payload = {
        "login_id": my_id,
        "password": my_pw,
    }

    session = requests.Session()
    t_start = time.time()

    try:
        # 1. 로그인
        if (
            session.post(
                LOGIN_URL,
                json=payload,
                timeout=5,
            ).status_code
            != 200
        ):
            return False, 0

        # 2. 과목 로딩
        if (
            session.get(
                COURSE_URL,
                timeout=5,
            ).status_code
            != 200
        ):
            return False, 0

        # 3. 시험 입장
        if (
            session.post(
                TEST_ENTER_URL,
                json={"course_id": 45},
                timeout=5,
            ).status_code
            not in [200, 201]
        ):
            return False, 0

        # 4. 답안 제출
        if (
            session.post(
                TEST_STOP_URL,
                json={"course_id": 45},
                timeout=5,
            ).status_code
            != 200
        ):
            return False, 0

        # 5. 재응시 초기화
        if (
            session.post(
                TEST_RESET_URL,
                json={"course_id": 45},
                timeout=5,
            ).status_code
            != 200
        ):
            return False, 0

        total_latency = round(
            (time.time() - t_start) * 1000
        )

        return True, total_latency

    except Exception:
        return False, 0


# --- Pytest 테스트 케이스 영역 ---


@pytest.mark.parametrize(
    "target_users",
    [5, 10, 20, 30],
)
def test_load_profile_with_pytest(target_users):
    accounts = load_accounts_from_csv()

    if len(accounts) < target_users:
        pytest.skip(
            f"계정 수 부족으로 "
            f"{target_users}명 테스트 생략"
        )

    # 유저당 3회 루프 검증
    total_requests = target_users * 3

    success_count = 0
    fail_count = 0
    all_latencies = []

    print(
        f"\n[Pytest 부하 프로필] "
        f"{target_users}명 동시 접속 테스트 시작 "
        f"(Loop 3회)"
    )

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=target_users
    ) as executor:

        # Loop 3회 반복
        for _ in range(3):

            futures = [
                executor.submit(
                    execute_single_user_flow,
                    accounts[i],
                )
                for i in range(target_users)
            ]

            for future in concurrent.futures.as_completed(
                futures
            ):
                is_success, latency = future.result()

                if is_success:
                    success_count += 1
                    all_latencies.append(latency)
                else:
                    fail_count += 1

    # 지표 계산
    error_rate = (
        fail_count / total_requests
    ) * 100

    avg_latency = (
        sum(all_latencies) / len(all_latencies)
        if all_latencies
        else 0
    )

    print(
        f"👉 결과 -> 에러율: "
        f"{error_rate:.2f}% | "
        f"평균 Latency: "
        f"{round(avg_latency)}ms"
    )

    # 1. 에러율 기준 검증
    assert error_rate < 1.0, (
        f"부하 테스트 실패: "
        f"에러율이 1%를 초과했습니다 "
        f"({error_rate}%)"
    )

    # 2. 단계별 평균 Latency 기준 동적 검증
    if target_users == 5:
        max_allowed_latency = 1000

    elif target_users == 10:
        max_allowed_latency = 2000

    else:
        max_allowed_latency = 5000

    assert avg_latency < max_allowed_latency, (
        f"부하 테스트 실패: "
        f"{target_users}명 환경에서 "
        f"평균 Latency({round(avg_latency)}ms)가 "
        f"허용 기준치("
        f"{max_allowed_latency}ms)를 초과했습니다."
    )