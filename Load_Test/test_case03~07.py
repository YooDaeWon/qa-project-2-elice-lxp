import requests
import time
import concurrent.futures
import csv
import pytest

# API 엔드포인트 정의
LOGIN_URL = "https://dev-qatrack-api.dev.elicer.io/global/auth/login/"
COURSE_URL = "https://dev-qatrack-api.dev.elicer.io/acl/course/get/"
TEST_ENTER_URL = "https://dev-qatrack-api.dev.elicer.io/org/{org}/lecture/test/enter/"
TEST_STOP_URL = (
    "https://dev-qatrack-api.dev.elicer.io/org/{org}/lecture/test/reset/by_self/"
)
TEST_RESET_URL = "https://dev-qatrack-api.dev.elicer.io/org/{org}/lecture/test/reset/"


def load_accounts_from_csv(file_path="QA6test_account_list_(30).csv"):
    accounts = []
    with open(file_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            accounts.append(row)
    return accounts


def execute_sequential_flow(my_account, user_index):
    my_id = my_account.get("login_id")
    my_pw = my_account.get("password")
    payload = {"login_id": my_id, "password": my_pw}

    session = requests.Session()
    print(f"[{user_index + 1:02d}번 유저] 🚀 전체 트랜잭션 플로우 시작 ({my_id})")

    try:
        # [Step 0] 로그인 및 인증 세션 획득
        login_res = session.post(LOGIN_URL, json=payload, timeout=5)
        if login_res.status_code != 200:
            print(f"  └ ❌ 로그인 실패 (상태코드: {login_res.status_code})")
            return False

        # [LOAD-01 / Step 1] 과목 정보 로딩
        t1 = time.time()
        res_course = session.get(COURSE_URL, timeout=5)
        lat_course = round((time.time() - t1) * 1000)
        if res_course.status_code == 200:
            print(f"  └ [1단계 통과] 과목 정보 로딩 성공 ({lat_course}ms)")
        else:
            print(f"  └ [1단계 실패] 과목 로딩 상태코드: {res_course.status_code}")
            return False

        # [LOAD-02 / Step 2] 동시 시험 입장
        t2 = time.time()
        res_enter = session.post(TEST_ENTER_URL, json={"course_id": 45}, timeout=5)
        lat_enter = round((time.time() - t2) * 1000)
        if res_enter.status_code in [200, 201]:
            print(f"  └ [2단계 통과] 시험 입장 성공 ({lat_enter}ms)")
        else:
            print(f"  └ [2단계 실패] 시험 입장 상태코드: {res_enter.status_code}")
            return False

        # [LOAD-03 / Step 3] 동시 시험 답안 제출 (reset/by_self)
        t3 = time.time()
        res_stop = session.post(TEST_STOP_URL, json={"course_id": 45}, timeout=5)
        lat_stop = round((time.time() - t3) * 1000)
        if res_stop.status_code == 200:
            print(f"  └ [3단계 통과] 답안 제출 성공 ({lat_stop}ms)")
        else:
            print(f"  └ [3단계 실패] 답안 제출 상태코드: {res_stop.status_code}")
            return False

        # [LOAD-04 / Step 4] 시험 재응시 세션 초기화
        t4 = time.time()
        res_reset = session.post(TEST_RESET_URL, json={"course_id": 45}, timeout=5)
        lat_reset = round((time.time() - t4) * 1000)
        if res_reset.status_code == 200:
            print(f"  └ [4단계 통과] 재응시 초기화 성공 ({lat_reset}ms) ✨ [완주 완료]")
            return True
        else:
            print(f"  └ [4단계 실패] 재응시 초기화 상태코드: {res_reset.status_code}")
            return False

    except requests.exceptions.Timeout:
        print(f"  └ 🚨 [타임아웃] 5초 초과로 비상 중단 (Kill Switch)")
        return False
    except Exception as e:
        print(f"  └ 🚨 [에러 발생] {e}")
        return False


# --- Pytest 테스트 영역 ---


@pytest.mark.parametrize("user_count", [5, 10, 20, 30])
def test_load_sequential_flow(user_count):
    accounts = load_accounts_from_csv()
    if len(accounts) < user_count:
        pytest.skip(f"🚨 계정 부족 (필요: {user_count}, 보유: {len(accounts)})")

    print(
        f"\n=== 가상 유저 {user_count}명 동시 투입: 1~4단계 연쇄 트랜잭션 테스트 시작 ==="
    )

    success_count = 0
    fail_count = 0

    # 30개 계정을 활용해 병렬(동시) 실행
    with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
        futures = [
            executor.submit(execute_sequential_flow, accounts[i], i)
            for i in range(user_count)
        ]

        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1
            else:
                fail_count += 1

    # 지표 산출
    total_requests = user_count
    error_rate = (fail_count / total_requests) * 100

    print(f"📊 [결과 요약 - {user_count}명 부하]")
    print(f"  - 성공: {success_count}명 | 실패: {fail_count}명")
    print(f"  - 에러율: {error_rate:.2f}%\n")

    # Pytest 검증 기준 (계획서 기준: 에러율 1% 미만)
    assert error_rate < 1.0, (
        f"부하 테스트 실패: {user_count}명 환경에서 에러율이 1%를 초과했습니다 ({error_rate}%)"
    )
