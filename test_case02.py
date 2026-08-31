import requests
import time
import concurrent.futures
import csv
import pytest

LOGIN_URL = "https://dev-qatrack-api.dev.elicer.io/global/auth/login/"
COURSE_URL = "https://dev-qatrack-api.dev.elicer.io/acl/course/get/"


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


def user_flow_with_token(my_account, user_index):
    """
    [핵심 흐름]
    1. 로그인 요청
    2. 응답 JSON에서 세션/토큰 동적 추출
    3. 추출한 토큰을 헤더에 담아 후속 API 호출 후 성공 여부(True/False) 반환
    """
    my_id = my_account.get("login_id")
    my_pw = my_account.get("password")
    payload = {"login_id": my_id, "password": my_pw}

    session = requests.Session()

    try:
        # 1단계: 로그인 수행
        login_res = session.post(LOGIN_URL, json=payload, timeout=5)

        if login_res.status_code == 200:
            res_data = login_res.json()

            # 2단계: 응답 데이터에서 토큰 동적 추출
            token = res_data.get("eliceSessionKey") or res_data.get("token")

            # 3단계: 추출된 토큰을 헤더에 장착 후 후속 API 호출
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            start_time = time.time()
            course_res = session.get(COURSE_URL, headers=headers, timeout=5)
            latency = round((time.time() - start_time) * 1000)

            if course_res.status_code == 200:
                print(
                    f"[{user_index + 1:02d}번 유저] 🟢 로그인 및 토큰 연계 과목 조회 성공 | 응답시간: {latency}ms"
                )
                return True
            else:
                print(
                    f"[{user_index + 1:02d}번 유저] 🟡 로그인 성공했으나 후속 API 실패 (상태코드: {course_res.status_code})"
                )
                return False
        else:
            print(
                f"[{user_index + 1:02d}번 유저] 🔴 로그인 실패 (상태코드: {login_res.status_code})"
            )
            return False

    except Exception as e:
        print(f"[{user_index + 1:02d}번 유저] 🚨 에러 발생: {e}")
        return False


# --- Pytest 테스트 영역 ---


@pytest.mark.parametrize("user_count", [5, 10, 20, 30])
def test_token_extraction_with_pytest(user_count):
    accounts = load_accounts_from_csv()
    if not accounts:
        pytest.fail("🚨 CSV 파일에서 계정을 하나도 읽지 못했습니다.")

    if len(accounts) < user_count:
        pytest.skip(f"🚨 계정 수가 부족하여 {user_count}명 테스트를 생략합니다.")

    print(f"\n=== {user_count}명 토큰 동적 추출 및 후속 API 연동 부하 테스트 시작 ===")

    success_count = 0
    fail_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
        futures = [
            executor.submit(user_flow_with_token, accounts[i], i)
            for i in range(user_count)
        ]

        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1
            else:
                fail_count += 1

    # 지표 산출
    error_rate = (fail_count / user_count) * 100

    print(f"\n📊 [결과 요약 - {user_count}명 토큰 연동 부하]")
    print(f"  - 성공: {success_count}명 | 실패: {fail_count}명")
    print(f"  - 에러율: {error_rate:.2f}%\n")

    # Pytest 검증 (계획서 기준: 에러율 1% 미만)
    assert error_rate < 1.0, (
        f"토큰 연동 부하 테스트 실패: {user_count}명 환경에서 에러율이 1%를 초과했습니다 ({error_rate}%)"
    )
