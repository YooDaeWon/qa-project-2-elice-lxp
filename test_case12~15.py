import requests
import time
import concurrent.futures
import csv
import random
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


def execute_safety_controlled_flow(my_account, user_index):
    """
    [안전성 통제 로직 반영]
    1. Loop Count 최대 3회 제한 준수
    2. Sampler 간 3~5초 임의 지연 (Timer 지연 간격 준수)
    3. 500 에러 발생 시 즉시 중단 (Kill Switch)
    4. 응답 지연 시간(Latency) 5,000ms 초과 시 즉시 중단
    """
    my_id = my_account.get("login_id")
    my_pw = my_account.get("password")
    payload = {"login_id": my_id, "password": my_pw}

    session = requests.Session()
    completed_loops = 0

    # [통제 항목 3] Loop Count 정확히 3회 제한 (Infinite 방지)
    for loop in range(1, 4):
        try:
            # 모든 개별 요청마다 Latency 5초 초과 및 500 에러 체크용 내부 함수
            def send_request_with_safety_check(method, url, **kwargs):
                t_start = time.time()
                if method == "POST":
                    res = session.post(url, **kwargs)
                else:
                    res = session.get(url, **kwargs)

                latency_ms = (time.time() - t_start) * 1000

                # [통제 항목 2] Latency 5초(5000ms) 초과 시 즉시 스크립트 중단 (Kill Switch)
                if latency_ms > 5000:
                    raise Exception(
                        f"🚨 [안전성 통제 발동] Latency 5초 초과 감지 ({round(latency_ms)}ms) -> 테스트 즉시 중단"
                    )

                # [통제 항목 1] 500 Internal Server Error 발생 시 즉시 중단 (Kill Switch)
                if res.status_code == 500:
                    raise Exception(
                        f"🚨 [안전성 통제 발동] 500 에러 발생 감지 -> 테스트 즉시 중단"
                    )

                return res

            # 1. 로그인
            res_login = send_request_with_safety_check(
                "POST", LOGIN_URL, json=payload, timeout=6
            )
            if res_login.status_code != 200:
                return False, f"로그인 실패 (상태코드: {res_login.status_code})"

            # 2. 과목 로딩
            res_course = send_request_with_safety_check("GET", COURSE_URL, timeout=6)
            if res_course.status_code != 200:
                return False, f"과목 로딩 실패 (상태코드: {res_course.status_code})"

            # 3. 시험 입장
            res_enter = send_request_with_safety_check(
                "POST", TEST_ENTER_URL, json={"course_id": 45}, timeout=6
            )
            if res_enter.status_code not in [200, 201]:
                return False, f"시험 입장 실패 (상태코드: {res_enter.status_code})"

            # 4. 답안 제출
            res_stop = send_request_with_safety_check(
                "POST", TEST_STOP_URL, json={"course_id": 45}, timeout=6
            )
            if res_stop.status_code != 200:
                return False, f"답안 제출 실패 (상태코드: {res_stop.status_code})"

            # 5. 재응시 초기화
            res_reset = send_request_with_safety_check(
                "POST", TEST_RESET_URL, json={"course_id": 45}, timeout=6
            )
            if res_reset.status_code != 200:
                return False, f"재응시 초기화 실패 (상태코드: {res_reset.status_code})"

            completed_loops += 1

            # [통제 항목 4] Timer 지연 간격 준수: Sampler 간 3초 ~ 5초 임의 지연 적용 (연타 방지)
            if loop < 3:
                delay_time = random.uniform(3.0, 5.0)
                time.sleep(delay_time)

        except Exception as e:
            # 통제 조건에 걸려 예외가 발생한 경우 즉시 실패 처리 및 루프 탈출
            return False, str(e)

    # 무한 루프 없이 정확히 3회 수행 후 정상 종료 여부 확인
    if completed_loops == 3:
        return True, "정상 완료"
    else:
        return False, "루프 횟수 미달"


# --- Pytest 테스트 영역 ---


@pytest.mark.parametrize("target_users", [5, 10, 20, 30])
def test_safety_controls_with_pytest(target_users):
    accounts = load_accounts_from_csv()
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
            executor.submit(execute_safety_controlled_flow, accounts[i], i)
            for i in range(target_users)
        ]

        for future in concurrent.futures.as_completed(futures):
            is_success, reason = future.result()
            if is_success:
                success_count += 1
            else:
                fail_count += 1
                failure_reasons.append(reason)

    error_rate = (fail_count / target_users) * 100

    print(f"\n📊 [안전성 검증 결과 요약 - {target_users}명]")
    print(f"  - 성공: {success_count}명 | 실패: {fail_count}명")
    print(f"  - 에러율: {error_rate:.2f}%")
    if failure_reasons:
        print(f"  - 주요 중단/에러 사유 예시: {failure_reasons[0]}\n")

    # Pytest 에러율 기준 검증 (< 1%)
    assert error_rate < 1.0, (
        f"안전성 통제 검증 실패: {target_users}명 환경에서 허용 에러율(1%)을 초과했거나 "
        f"안전성 통제(Kill Switch 등)에 의해 테스트가 중단되었습니다. 사유: {failure_reasons}"
    )
