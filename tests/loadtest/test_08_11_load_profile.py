import allure
import concurrent.futures
import time

import pytest

from framework.loadtest.client import LoadClient
from framework.loadtest.pacing import pause_after_stage, ramp_up_wait, think_time
from framework.loadtest.report import attach_load_summary


pytestmark = [
    pytest.mark.load_profile,
    allure.label("owner", "leehyomin"),
    allure.label("team", "QA4"),
]

LOOP_COUNT = 3


def execute_single_user_flow(account, user_index, user_count, loop):
    """단일 유저가 1~4단계를 1회 완주 (Loop 단위 로그 포함)"""
    ramp_up_wait(user_index, user_count)
    login_id = account.get("login_id")
    password = account.get("password")
    client = LoadClient()
    api_elapsed = 0.0
    tag = f"[Loop {loop}/{LOOP_COUNT}][{user_index + 1:02d}번]"

    try:
        print(f"{tag} 👤 {login_id} 동시 로그인 시도")
        started = time.time()
        login_response = client.auth.login(login_id, password)
        login_ms = round((time.time() - started) * 1000)
        api_elapsed += login_ms / 1000
        if login_response.status_code != 200:
            print(
                f"{tag} 🔴 로그인 실패 | status={login_response.status_code} | "
                f"{login_ms}ms | body={login_response.text[:200]}"
            )
            return False, 0, "login"

        print(f"{tag} 🟢 로그인 성공 | {login_ms}ms")

        think_time()
        started = time.time()
        course_response = client.course.get_course()
        course_ms = round((time.time() - started) * 1000)
        api_elapsed += course_ms / 1000
        if course_response.status_code != 200:
            print(
                f"{tag} 🔴 과목 조회 실패 | status={course_response.status_code} | {course_ms}ms"
            )
            return False, 0, "course"
        print(f"{tag} 🟢 과목 조회 성공 | {course_ms}ms")

        think_time()
        started = time.time()
        enter_response = client.exam.enter()
        enter_ms = round((time.time() - started) * 1000)
        api_elapsed += enter_ms / 1000
        if enter_response.status_code not in [200, 201]:
            print(
                f"{tag} 🔴 시험 입장 실패 | status={enter_response.status_code} | {enter_ms}ms"
            )
            return False, 0, "enter"
        print(f"{tag} 🟢 시험 입장 성공 | {enter_ms}ms")

        think_time()
        started = time.time()
        submit_response = client.exam.submit()
        submit_ms = round((time.time() - started) * 1000)
        api_elapsed += submit_ms / 1000
        if submit_response.status_code != 200:
            print(
                f"{tag} 🔴 답안 제출 실패 | status={submit_response.status_code} | {submit_ms}ms"
            )
            return False, 0, "submit"
        print(f"{tag} 🟢 답안 제출 성공 | {submit_ms}ms")

        think_time()
        started = time.time()
        reset_response = client.exam.reset()
        reset_ms = round((time.time() - started) * 1000)
        api_elapsed += reset_ms / 1000
        if reset_response.status_code != 200:
            print(
                f"{tag} 🔴 재응시 초기화 실패 | status={reset_response.status_code} | {reset_ms}ms"
            )
            return False, 0, "reset"

        total_ms = round(api_elapsed * 1000)
        print(
            f"{tag} ✨ 완주 | login={login_ms}ms course={course_ms}ms "
            f"enter={enter_ms}ms submit={submit_ms}ms reset={reset_ms}ms "
            f"api합계={total_ms}ms"
        )
        return True, total_ms, None
    except Exception as error:
        print(f"{tag} 🚨 예외 | {login_id}: {error}")
        return False, 0, "exception"


@pytest.mark.parametrize("target_users", [5, 10, 20, 30])
@allure.label("tc_id", "08")
def test_id_08_11_load_profile(accounts, target_users):
    """ID 8~11 동시 접속 부하 프로필 (Loop 3회)"""
    if len(accounts) < target_users:
        pytest.skip(f"계정 수 부족으로 {target_users}명 테스트 생략")

    total_requests = target_users * LOOP_COUNT
    success_count = 0
    fail_count = 0
    all_latencies = []
    loop_summaries = []
    fail_steps = {}

    print(
        f"\n=== [Loop 3회 동시 로그인·트랜잭션] {target_users}명 시작 "
        f"(총 요청 {total_requests}회 = {target_users}명 × {LOOP_COUNT}루프) ==="
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=target_users) as executor:
        for loop in range(1, LOOP_COUNT + 1):
            loop_ok = 0
            loop_fail = 0
            loop_latencies = []
            loop_started = time.time()

            print(f"\n--- Loop {loop}/{LOOP_COUNT} | 동시 유저 {target_users}명 ---")

            futures = [
                executor.submit(
                    execute_single_user_flow,
                    accounts[index],
                    index,
                    target_users,
                    loop,
                )
                for index in range(target_users)
            ]
            for future in concurrent.futures.as_completed(futures):
                is_success, latency, fail_step = future.result()
                if is_success:
                    success_count += 1
                    loop_ok += 1
                    all_latencies.append(latency)
                    loop_latencies.append(latency)
                else:
                    fail_count += 1
                    loop_fail += 1
                    step = fail_step or "unknown"
                    fail_steps[step] = fail_steps.get(step, 0) + 1

            loop_elapsed = round(time.time() - loop_started, 2)
            loop_error_rate = (loop_fail / target_users) * 100
            loop_avg = (
                sum(loop_latencies) / len(loop_latencies) if loop_latencies else 0
            )
            summary = {
                "loop": loop,
                "success": loop_ok,
                "fail": loop_fail,
                "error_rate": round(loop_error_rate, 2),
                "avg_latency_ms": round(loop_avg),
                "wall_seconds": loop_elapsed,
            }
            loop_summaries.append(summary)
            print(
                f"📊 Loop {loop} 요약 | 성공 {loop_ok}/{target_users} | "
                f"실패 {loop_fail} | 에러율 {loop_error_rate:.2f}% | "
                f"평균 API Latency {round(loop_avg)}ms | 소요 {loop_elapsed}s"
            )

            if loop < LOOP_COUNT:
                print("  └ ⏳ 다음 Loop 전 think time 3~5초")
                think_time()

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
        loop_summaries=loop_summaries,
        fail_steps=fail_steps,
    )

    print(f"\n📊 [최종 요약 - {target_users}명 × Loop {LOOP_COUNT}]")
    print(f"  - 성공: {success_count} | 실패: {fail_count} | 총요청: {total_requests}")
    print(f"  - 에러율: {error_rate:.2f}% | 평균 API Latency: {round(avg_latency)}ms")
    if fail_steps:
        print(f"  - 실패 단계 집계: {fail_steps}")
    for item in loop_summaries:
        print(
            f"  - Loop {item['loop']}: 성공 {item['success']}/{target_users}, "
            f"에러율 {item['error_rate']}%, 평균 {item['avg_latency_ms']}ms"
        )
    print()

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
    pause_after_stage(target_users)
