"""HAR 원본에서 대조용 요약본(data/har_summary.json)을 생성한다

원본 HAR은 수십~수백 MB에 인증 토큰까지 담기므로 저장소에 두지 않는다.
대조에 필요한 method/host/path만 뽑아 요약본으로 만들어 커밋한다.

사용법:
    python scripts/build_har_summary.py <har_파일경로> [--role educator]

새로 HAR을 수집했을 때만 실행하면 되고, 테스트 실행 시에는 필요 없다.
"""

import argparse
import collections
import json
from pathlib import Path
from urllib.parse import urlparse

try:
    import ijson
except ImportError:  # pragma: no cover
    ijson = None


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "data" / "har_summary.json"


def iter_entries(har_path):
    """HAR 항목을 하나씩 읽는다 (대용량 파일은 스트리밍 파싱)"""
    if ijson is not None:
        with open(har_path, "rb") as har_file:
            for entry in ijson.items(har_file, "log.entries.item"):
                yield entry
        return

    # ijson이 없으면 전체 로드 (메모리 사용량 주의)
    data = json.loads(Path(har_path).read_text(encoding="utf-8", errors="replace"))
    for entry in data.get("log", {}).get("entries", []):
        yield entry


def build_summary(har_path, role):
    """HAR에서 호출 요약을 만든다 (인증 토큰 등 헤더·본문은 제외)"""
    aggregated = collections.Counter()
    total = 0
    hosts = set()

    for entry in iter_entries(har_path):
        url = entry.get("request", {}).get("url", "")
        if not url:
            continue
        total += 1
        parsed = urlparse(url)
        hosts.add(parsed.netloc)
        aggregated[
            (entry["request"].get("method", ""), parsed.netloc, parsed.path)
        ] += 1

    return {
        "source": Path(har_path).name,
        "captured_by": role,
        "total_calls": total,
        "total_hosts": len(hosts),
        "calls": [
            {"method": method, "host": host, "path": path, "count": count}
            for (method, host, path), count in sorted(
                aggregated.items(), key=lambda item: (item[0][1], item[0][2], item[0][0])
            )
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="HAR 요약본 생성")
    parser.add_argument("har_path", help="원본 HAR 파일 경로")
    parser.add_argument(
        "--role", default="educator", help="수집에 사용한 계정 권한 (기본: educator)"
    )
    args = parser.parse_args()

    summary = build_summary(args.har_path, args.role)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(f"총 호출 {summary['total_calls']}건 / 호스트 {summary['total_hosts']}개")
    print(f"고유 호출 {len(summary['calls'])}건 → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
