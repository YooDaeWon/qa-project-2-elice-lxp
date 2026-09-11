import allure
import concurrent.futures
import time

import pytest

from framework.loadtest.client import LoadClient
from framework.loadtest.pacing import pause_after_stage, ramp_up_wait, think_time
from framework.loadtest.report import attach_load_summary


pytestmark = [
    pytest.mark.load_transaction,
    allure.label("owner", "leehyomin"),
    allure.label("team", "QA4"),
]


def execute_sequential_flow(account, user_index, user_count):
    """로그인부터 재응시 초기화까지 1~4단계 트랜잭션"""
    ramp_up_wait(user_index, user_count)
    login_id = account.get("login_id")
    password = account.get("password")
    client = LoadClient()

    print(f"[{user_index + 1:02d}번 유저] 🚀 전체 트랜잭션 플로우 시작 ({login_id})")

    try:
        login_response = client.auth.login(login_id, password)
        if login_response.status_code != 200:
            print(f"  └ ❌ 로그인 실패 (상태코드: {login_response.status_code})")
            return False

        think_time()
        start_time = time.time()
        course_response = client.course.get_course()
        latency = round((time.time() - start_time) * 1000)
        if course_response.status_code == 200:
            print(f"  └ [1단계 통과] 과목 정보 로딩 성공 ({latency}ms)")
        else:
            print(f"  └ [1단계 실패] 과목 로딩 상태코드: {course_response.status_code}")
            return False

        think_time()
        start_time = time.time()
        enter_response = client.exam.enter()
        latency = round((time.time() - start_time) * 1000)
        if enter_response.status_code in [200, 201]:
            print(f"  └ [2단계 통과] 시험 입장 성공 ({latency}ms)")
        else:
            print(f"  └ [2단계 실패] 시험 입장 상태코드: {enter_response.status_code}")
            return False

        think_time()
        start_time = time.time()
        submit_response = client.exam.submit()
        latency = round((time.time() - start_time) * 1000)
        if submit_response.status_code == 200:
            print(f"  └ [3단계 통과] 답안 제출 성공 ({latency}ms)")
        else:
            print(f"  └ [3단계 실패] 답안 제출 상태코드: {submit_response.status_code}")
            return False

        think_time()
        start_time = time.time()
        reset_response = client.exam.reset()
        latency = round((time.time() - start_time) * 1000)
        if reset_response.status_code == 200:
            print(f"  └ [4단계 통과] 재응시 초기화 성공 ({latency}ms) ✨ [완주 완료]")
            return True

        print(f"  └ [4단계 실패] 재응시 초기화 상태코드: {reset_response.status_code}")
        return False
    except Exception as error:
        print(f"  └ 🚨 [에러 발생] {error}")
        return False


@pytest.mark.parametrize("user_count", [5, 10, 20, 30])
@allure.label("tc_id", "03")
def test_id_03_07_transaction_flow(accounts, user_count):
    """ID 3~7 1~4단계 연쇄 트랜잭션 부하"""
    if len(accounts) < user_count:
        pytest.skip(f"🚨 계정 부족 (필요: {user_count}, 보유: {len(accounts)})")

    print(
        f"\n=== 가상 유저 {user_count}명 동시 투입: 1~4단계 연쇄 트랜잭션 테스트 시작 ==="
    )

    success_count = 0
    fail_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
        futures = [
            executor.submit(
                execute_sequential_flow, accounts[index], index, user_count
            )
            for index in range(user_count)
        ]

        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1
            else:
                fail_count += 1

    error_rate = (fail_count / user_count) * 100
    attach_load_summary(
        "트랜잭션 부하 지표",
        user_count=user_count,
        success_count=success_count,
        fail_count=fail_count,
        error_rate=round(error_rate, 2),
    )

    print(f"📊 [결과 요약 - {user_count}명 부하]")
    print(f"  - 성공: {success_count}명 | 실패: {fail_count}명")
    print(f"  - 에러율: {error_rate:.2f}%\n")

    assert error_rate < 1.0, (
        f"부하 테스트 실패: {user_count}명 환경에서 에러율이 1%를 초과했습니다 ({error_rate}%)"
    )
    pause_after_stage(user_count)
