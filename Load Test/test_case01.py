import requests
import time
import concurrent.futures
import csv
import pytest

LOGIN_URL = "https://dev-qatrack-api.dev.elicer.io/global/auth/login/"


def load_accounts_from_csv(file_path="QA6test_account_list_(30).csv"):
    accounts = []
    try:
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                accounts.append(row)
    except FileNotFoundError:
        print(f"🚨 {file_path} 파일을 찾을 수 없습니다.")
    return accounts


def login_with_dummy_account(my_account, user_index):
    """단일 유저의 로그인 요청을 수행하고 성공 여부(True/False)를 반환합니다."""
    my_id = my_account.get("login_id")
    my_pw = my_account.get("password")

    payload = {"login_id": my_id, "password": my_pw}
    print(f"[{user_index + 1:02d}번 유저] 👤 {my_id} 로그인 시도 중...")

    start_time = time.time()
    try:
        response = requests.post(LOGIN_URL, json=payload, timeout=5)
        latency = round((time.time() - start_time) * 1000)

        if response.status_code == 200:
            print(f"  └ 🟢 [성공] {my_id} | 응답시간: {latency}ms")
            return True
        else:
            print(
                f"  └ 🔴 [실패] {my_id} | 상태코드: {response.status_code} | 응답내용: {response.text}"
            )
            return False

    except requests.exceptions.Timeout:
        print(f"  └ 🚨 [타임아웃] {my_id} (5초 초과)")
        return False
    except Exception as e:
        print(f"  └ 🚨 [에러 발생] {my_id}: {e}")
        return False


# --- Pytest 테스트 케이스 영역 ---


@pytest.mark.parametrize("user_count", [5, 10, 20, 30])
def test_login_load_with_pytest(user_count):
    accounts = load_accounts_from_csv()

    print(f"\n🔍 [디버깅] CSV 파일에서 읽어온 총 계정 수: {len(accounts)}개")
    if not accounts:
        pytest.fail("🚨 CSV 파일에서 계정을 하나도 읽지 못했습니다.")

    if len(accounts) < user_count:
        pytest.skip(f"🚨 계정 수가 부족하여 {user_count}명 테스트를 생략합니다.")

    print(f"=== {user_count}명 단계적 동시 접속 로그인 테스트 시작 ===")

    success_count = 0
    fail_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
        futures = [
            executor.submit(login_with_dummy_account, accounts[i], i)
            for i in range(user_count)
        ]

        for future in concurrent.futures.as_completed(futures):
            try:
                if future.result():
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                print(f"🚨 스레드 에러 발생: {e}")
                fail_count += 1

    # 지표 산출
    error_rate = (fail_count / user_count) * 100

    print(f"\n📊 [결과 요약 - {user_count}명 로그인 부하]")
    print(f"  - 성공: {success_count}명 | 실패: {fail_count}명")
    print(f"  - 에러율: {error_rate:.2f}%\n")

    # Pytest 검증 (계획서 기준: 에러율 1% 미만)
    assert error_rate < 1.0, (
        f"로그인 부하 테스트 실패: {user_count}명 환경에서 에러율이 1%를 초과했습니다 ({error_rate}%)"
    )
