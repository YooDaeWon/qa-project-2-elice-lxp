import concurrent.futures
import time

import pytest
import requests

from framework.loadtest.client import LoadClient
from framework.loadtest.report import attach_load_summary


pytestmark = pytest.mark.load_login


def login_with_dummy_account(account, user_index):
    """단일 유저 로그인 요청"""
    login_id = account.get("login_id")
    password = account.get("password")
    client = LoadClient()

    print(f"[{user_index + 1:02d}번 유저] 👤 {login_id} 로그인 시도 중...")

    start_time = time.time()
    try:
        response = client.auth.login(login_id, password)
        latency = round((time.time() - start_time) * 1000)

        if response.status_code == 200:
            print(f"  └ 🟢 [성공] {login_id} | 응답시간: {latency}ms")
            return True

        print(
            f"  └ 🔴 [실패] {login_id} | 상태코드: {response.status_code} | 응답내용: {response.text}"
        )
        return False
    except requests.exceptions.Timeout:
        print(f"  └ 🚨 [타임아웃] {login_id} (5초 초과)")
        return False
    except Exception as error:
        print(f"  └ 🚨 [에러 발생] {login_id}: {error}")
        return False


@pytest.mark.parametrize("user_count", [5, 10, 20, 30])
def test_id_01_login_load(accounts, user_count):
    """ID 1 단계적 동시 접속 로그인 부하"""
    print(f"\n🔍 [디버깅] CSV 파일에서 읽어온 총 계정 수: {len(accounts)}개")

    if len(accounts) < user_count:
        pytest.skip(f"🚨 계정 수가 부족하여 {user_count}명 테스트를 생략합니다.")

    print(f"=== {user_count}명 단계적 동시 접속 로그인 테스트 시작 ===")

    success_count = 0
    fail_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
        futures = [
            executor.submit(login_with_dummy_account, accounts[index], index)
            for index in range(user_count)
        ]

        for future in concurrent.futures.as_completed(futures):
            try:
                if future.result():
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as error:
                print(f"🚨 스레드 에러 발생: {error}")
                fail_count += 1

    error_rate = (fail_count / user_count) * 100
    attach_load_summary(
        "로그인 부하 지표",
        user_count=user_count,
        success_count=success_count,
        fail_count=fail_count,
        error_rate=round(error_rate, 2),
    )

    print(f"\n📊 [결과 요약 - {user_count}명 로그인 부하]")
    print(f"  - 성공: {success_count}명 | 실패: {fail_count}명")
    print(f"  - 에러율: {error_rate:.2f}%\n")

    assert error_rate < 1.0, (
        f"로그인 부하 테스트 실패: {user_count}명 환경에서 에러율이 1%를 초과했습니다 ({error_rate}%)"
    )
