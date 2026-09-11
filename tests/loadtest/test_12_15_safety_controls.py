import allure
import concurrent.futures

import pytest
import requests

from framework.loadtest.client import LoadClient
from framework.loadtest.pacing import pause_after_stage, ramp_up_wait, think_time
from framework.loadtest.report import attach_load_summary
from framework.loadtest.safety import SafetyKillSwitchError, SafetySession


pytestmark = [
    pytest.mark.load_safety,
    allure.label("owner", "leehyomin"),
    allure.label("team", "QA4"),
]


def execute_safety_controlled_flow(account, user_index, user_count):
    """Loop 3회, Timer 지연, Kill Switch가 적용된 트랜잭션"""
    ramp_up_wait(user_index, user_count)
    login_id = account.get("login_id")
    password = account.get("password")
    session = requests.Session()
    client = LoadClient(session=SafetySession(session))
    completed_loops = 0

    for loop in range(1, 4):
        try:
            login_response = client.auth.login(login_id, password)
            if login_response.status_code != 200:
                return False, f"로그인 실패 (상태코드: {login_response.status_code})"

            think_time()
            course_response = client.course.get_course()
            if course_response.status_code != 200:
                return False, f"과목 로딩 실패 (상태코드: {course_response.status_code})"

            think_time()
            enter_response = client.exam.enter()
            if enter_response.status_code not in [200, 201]:
                return False, f"시험 입장 실패 (상태코드: {enter_response.status_code})"

            think_time()
            submit_response = client.exam.submit()
            if submit_response.status_code != 200:
                return False, f"답안 제출 실패 (상태코드: {submit_response.status_code})"

            think_time()
            reset_response = client.exam.reset()
            if reset_response.status_code != 200:
                return (
                    False,
                    f"재응시 초기화 실패 (상태코드: {reset_response.status_code})",
                )

            completed_loops += 1

            if loop < 3:
                think_time()
        except SafetyKillSwitchError as error:
            return False, str(error)
        except Exception as error:
            return False, str(error)

    if completed_loops == 3:
        return True, "정상 완료"

    return False, "루프 횟수 미달"


@pytest.mark.parametrize("target_users", [5, 10, 20, 30])
@allure.label("tc_id", "12")
def test_id_12_15_safety_controls(accounts, target_users):
    """ID 12~15 안전성 통제 검증"""
    if len(accounts) < target_users:
        pytest.skip(f"🚨 계정 수 부족으로 {target_users}명 테스트 생략")

    print(
        f"\n🛡️ [안전성 통제 검증] {target_users}명 동시 부하 테스트 시작 (Safety Controls 적용)"
    )

    success_count = 0
    fail_count = 0
    failure_reasons = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=target_users) as executor:
        futures = [
            executor.submit(
                execute_safety_controlled_flow, accounts[index], index, target_users
            )
            for index in range(target_users)
        ]

        for future in concurrent.futures.as_completed(futures):
            is_success, reason = future.result()
            if is_success:
                success_count += 1
            else:
                fail_count += 1
                failure_reasons.append(reason)

    error_rate = (fail_count / target_users) * 100
    attach_load_summary(
        "안전성 통제 지표",
        target_users=target_users,
        success_count=success_count,
        fail_count=fail_count,
        error_rate=round(error_rate, 2),
        failure_reasons=failure_reasons[:5],
    )

    print(f"\n📊 [안전성 검증 결과 요약 - {target_users}명]")
    print(f"  - 성공: {success_count}명 | 실패: {fail_count}명")
    print(f"  - 에러율: {error_rate:.2f}%")
    if failure_reasons:
        print(f"  - 주요 중단/에러 사유 예시: {failure_reasons[0]}\n")

    assert error_rate < 1.0, (
        f"안전성 통제 검증 실패: {target_users}명 환경에서 허용 에러율(1%)을 초과했거나 "
        f"안전성 통제(Kill Switch 등)에 의해 테스트가 중단되었습니다. 사유: {failure_reasons}"
    )
    pause_after_stage(target_users)
