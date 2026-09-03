import csv
from pathlib import Path


def load_accounts(file_path):
    """CSV에서 부하 테스트 계정 목록 읽기"""
    accounts = []
    csv_path = Path(file_path)

    if not csv_path.exists():
        print(f"🚨 {csv_path} 파일을 찾을 수 없습니다.")
        return accounts

    with csv_path.open(mode="r", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            accounts.append(row)

    return accounts
