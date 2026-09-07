import allure
import concurrent.futures
import time

import pytest

from framework.loadtest.client import LoadClient
from framework.loadtest.report import attach_load_summary


pytestmark = [
    pytest.mark.load_profile,
    allure.label("owner", "leehyomin"),
    allure.label("team", "QA4"),
]


def execute_single_user_flow(account):
    """단일 유저가 1~4단계를 1회 완주"""
    login_id = account.get("login_id")
    password = account.get("password")
    client = LoadClient()
    start_time = time.time()

    try:
        if client.auth.login(login_id, password).status_code != 200:
            return False, 0
        if client.course.get_course().status_code != 200:
            return False, 0
        if client.exam.enter().status_code not in [200, 201]:
            return False, 0
        if client.exam.submit().status_code != 200:
            return False, 0
        if client.exam.reset().status_code != 200:
            return False, 0

        total_latency = round((time.time() - start_time) * 1000)
        return True, total_latency
    except Exception:
        return False, 0


@pytest.mark.parametrize("target_users", [5, 10, 20, 30])
@allure.label("tc_id", "08")
def test_id_08_11_load_profile(accounts, target_users):
    """ID 8~11 동시 접속 부하 프로필"""
    if len(accounts) < target_users:
        pytest.skip(f"계정 수 부족으로 {target_users}명 테스트 생략")

    total_requests = target_users * 3
    success_count = 0
    fail_count = 0
    all_latencies = []

    print(f"\n[Pytest 부하 프로필] {target_users}명 동시 접속 테스트 시작 (Loop 3회)")

    with concurrent.futures.ThreadPoolExecutor(max_workers=target_users) as executor:
        for _ in range(3):
            futures = [
                executor.submit(execute_single_user_flow, accounts[index])
                for index in range(target_users)
            ]
            for future in concurrent.futures.as_completed(futures):
                is_success, latency = future.result()
                if is_success:
                    success_count += 1
                    all_latencies.append(latency)
                else:
                    fail_count += 1

    error_rate = (fail_count / total_requests) * 100
    avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0
    attach_load_summary(
        "부하 프로필 지표",
        target_users=target_users,
        total_requests=total_requests,
        success_count=success_count,
        fail_count=fail_count,
        error_rate=round(error_rate, 2),
        avg_latency_ms=round(avg_latency),
    )

    print(
        f"👉 결과 -> 에러율: {error_rate:.2f}% | 평균 Latency: {round(avg_latency)}ms"
    )

    assert error_rate < 1.0, (
        f"부하 테스트 실패: 에러율이 1%를 초과했습니다 ({error_rate}%)"
    )

    if target_users == 5:
        max_allowed_latency = 1000
    elif target_users == 10:
        max_allowed_latency = 2000
    else:
        max_allowed_latency = 5000

    assert avg_latency < max_allowed_latency, (
        f"부하 테스트 실패: {target_users}명 환경에서 평균 Latency({round(avg_latency)}ms)가 "
        f"허용 기준치({max_allowed_latency}ms)를 초과했습니다."
    )
