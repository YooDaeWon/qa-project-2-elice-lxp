import subprocess
import time
import os


def run_all_tests():
    test_files = [
        "test_case01.py",
        "test_case02.py",
        "test_case03~07.py",
        "test_case08~11.py",
        "test_case12~15.py",
    ]

    print("==================================================")
    print("🚀 [전체 통합 부하 테스트 러너] 시작합니다.")
    print("==================================================\n")

    start_time = time.time()

    # 2. 기존 allure-results 폴더 초기화 (선택 사항)
    if os.path.exists("allure-results"):
        for file in os.listdir("allure-results"):
            file_path = os.path.join("allure-results", file)
            if os.path.isfile(file_path):
                os.unlink(file_path)

    # 3. 파일별로 순차 실행 및 Allure 결과 수집
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"⚠️ [경고] '{test_file}' 파일을 찾을 수 없어 건너뜁니다.")
            continue

        print(f"▶️ 실행 중: {test_file} ...")

        # 각 파일을 pytest로 실행하면서 allure-results에 데이터를 누적시킵니다.
        cmd = ["pytest", f"--alluredir=allure-results", "-s", test_file]
        result = subprocess.run(cmd)

        if result.returncode == 0:
            print(f"✅ 완료: {test_file}\n")
        else:
            print(f"❌ 실패 또는 검증 기준 미달 발생: {test_file}\n")

    total_duration = round(time.time() - start_time, 2)
    print("==================================================")
    print(f"✨ 전체 통합 테스트가 종료되었습니다. (총 소요 시간: {total_duration}초)")
    print("==================================================")
    print("💡 대시보드 리포트를 보려면 아래 명령어를 입력하세요:")
    print("   allure generate allure-results -o allure-report --clean")
    print("   allure open allure-report")
    print("==================================================")


if __name__ == "__main__":
    run_all_tests()
