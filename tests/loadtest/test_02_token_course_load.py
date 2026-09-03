import concurrent.futures
import time

import pytest

from framework.loadtest.client import LoadClient
from framework.loadtest.report import attach_load_summary


pytestmark = pytest.mark.load_token


def user_flow_with_token(account, user_index):
    """로그인 후 토큰으로 과목 조회"""
    login_id = account.get("login_id")
    password = account.get("password")
    client = LoadClient()

    try:
        login_response = client.auth.login(login_id, password)
        if login_response.status_code != 200:
            print(
                f"[{user_index + 1:02d}번 유저] 🔴 로그인 실패 (상태코드: {login_response.status_code})"
            )
            return False

        token = client.auth.extract_token(login_response)
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        start_time = time.time()
        course_response = client.course.get_course(headers=headers)
        latency = round((time.time() - start_time) * 1000)

        if course_response.status_code == 200:
            print(
                f"[{user_index + 1:02d}번 유저] 🟢 로그인 및 토큰 연계 과목 조회 성공 | 응답시간: {latency}ms"
            )
            return True

        print(
            f"[{user_index + 1:02d}번 유저] 🟡 로그인 성공했으나 후속 API 실패 (상태코드: {course_response.status_code})"
        )
        return False
    except Exception as error:
        print(f"[{user_index + 1:02d}번 유저] 🚨 에러 발생: {error}")
        return False


@pytest.mark.parametrize("user_count", [5, 10, 20, 30])
def test_id_02_token_course_load(accounts, user_count):
    """ID 2 토큰 추출 및 과목 조회 부하"""
    if len(accounts) < user_count:
        pytest.skip(f"🚨 계정 수가 부족하여 {user_count}명 테스트를 생략합니다.")

    print(f"\n=== {user_count}명 토큰 동적 추출 및 후속 API 연동 부하 테스트 시작 ===")

    success_count = 0
    fail_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
        futures = [
            executor.submit(user_flow_with_token, accounts[index], index)
            for index in range(user_count)
        ]

        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1
            else:
                fail_count += 1

    error_rate = (fail_count / user_count) * 100
    attach_load_summary(
        "토큰 연동 부하 지표",
        user_count=user_count,
        success_count=success_count,
        fail_count=fail_count,
        error_rate=round(error_rate, 2),
    )

    print(f"\n📊 [결과 요약 - {user_count}명 토큰 연동 부하]")
    print(f"  - 성공: {success_count}명 | 실패: {fail_count}명")
    print(f"  - 에러율: {error_rate:.2f}%\n")

    assert error_rate < 1.0, (
        f"토큰 연동 부하 테스트 실패: {user_count}명 환경에서 에러율이 1%를 초과했습니다 ({error_rate}%)"
    )
