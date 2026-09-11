"""API 명세 ↔ 실제 호출(HAR) 대조 유틸

ID-47(명세 미등록 API 접근 통제) 검증의 근거를 만드는 모듈이다.

배경:
    제공된 기능 명세에 없는 엔드포인트(그림자 API)는 관리 대상에서 빠져 있어
    권한 검사가 누락된 채 열려 있을 수 있다. 이를 찾으려면 명세 전체와
    실제 호출 전체를 대조해야 한다.

입력 파일 (data/ 하위):
    - lxp_api_spec_강의실_자료.html : LXP 명세 (엔드포인트 386개)
    - lxp_api_spec_클래스.html      : classroom 명세 (엔드포인트 42개)
    - har_summary.json              : 실제 호출 요약 (원본 HAR에서 method/host/path만 추출)

HAR 원본은 용량이 크고 인증 토큰이 담기므로 저장소에 두지 않는다.
새로 수집했다면 scripts/build_har_summary.py로 요약본을 다시 만든다.
"""

import json
import re
from pathlib import Path


# 명세 HTML에서 엔드포인트 경로가 담기는 요소
EP_URL_PATTERN = re.compile(r'<span class="ep-url">(.*?)</span>')

# 명세가 다루는 호스트 (이 둘 외의 elice 백엔드 호출은 그림자 API)
SPEC_HOSTS = frozenset(
    {
        "dev-qatrack-classroom-api.dev.elicer.io",
        "dev-qatrack-api.dev.elicer.io",
    }
)

# elice 소유가 아닌 외부 서비스는 대조 대상이 아니다
ELICE_DOMAIN_SUFFIXES = (".elicer.io", ".elice.io")

# 백엔드 API가 아닌 호스트 (프론트 정적 자원·폰트·로깅 등)
NON_BACKEND_MARKERS = ("-web.", "static.", "font.", "markdown.", "frontend-logger.")

# LXP 경로 앞에 붙는 기관 접두어 (/org/academy/... → /...)
ORG_PREFIX_PATTERN = re.compile(r"^/org/[^/]+")


def load_spec_paths(spec_path):
    """명세 HTML에서 엔드포인트 경로 목록을 추출"""
    html = Path(spec_path).read_text(encoding="utf-8", errors="replace")
    return EP_URL_PATTERN.findall(html)


def _to_matcher(spec_path):
    """명세 경로를 정규식으로 변환 ({classroom_id} 같은 변수는 임의 세그먼트로 취급)"""
    escaped = re.escape(spec_path)
    # re.escape가 중괄호를 이스케이프하는 파이썬 버전 차이를 모두 처리
    pattern = re.sub(r"\\?\{[^}]+\\?\}", "[^/]+", escaped)
    return re.compile(f"^{pattern}/?$")


def is_elice_backend(host):
    """elice가 운영하는 백엔드 API 호스트인지 판별

    서드파티(google·facebook·sentry 등)와 프론트·정적 자원 호스트는 제외한다.
    """
    if not host.endswith(ELICE_DOMAIN_SUFFIXES):
        return False
    return not any(marker in host for marker in NON_BACKEND_MARKERS)


def load_har_calls(summary_path):
    """HAR 요약 파일에서 호출 목록을 읽어온다"""
    data = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    return data.get("calls", [])


def find_shadow_apis(spec_files, har_summary_path):
    """명세와 실제 호출을 대조해 그림자 API를 찾아낸다

    두 층위로 나눠 판정한다.
    - 호스트 단위: 명세가 아예 다루지 않는 백엔드 호스트
    - 경로 단위: 명세에 있는 호스트인데 그 안에서 명세에 없는 경로

    Returns:
        dict: shadow_hosts / shadow_paths / 집계값
    """
    matchers = {}
    for host, spec_file in spec_files.items():
        matchers[host] = [_to_matcher(path) for path in set(load_spec_paths(spec_file))]

    calls = load_har_calls(har_summary_path)
    backend_calls = [call for call in calls if is_elice_backend(call["host"])]

    shadow_hosts = {}
    shadow_paths = {}

    for call in backend_calls:
        host, path = call["host"], call["path"]

        if host not in SPEC_HOSTS:
            shadow_hosts.setdefault(host, 0)
            shadow_hosts[host] += call.get("count", 1)
            continue

        patterns = matchers.get(host, [])
        # LXP는 기관 접두어(/org/{org})를 떼고도 대조한다
        stripped = ORG_PREFIX_PATTERN.sub("", path)
        covered = any(
            matcher.match(path) or matcher.match(stripped) for matcher in patterns
        )
        if not covered:
            # 메서드가 달라도 같은 경로는 한 건으로 센다
            key = (host, path)
            shadow_paths.setdefault(key, 0)
            shadow_paths[key] += call.get("count", 1)

    return {
        "total_calls": len(calls),
        "backend_calls": len(backend_calls),
        "spec_endpoint_count": sum(
            len(load_spec_paths(spec_file)) for spec_file in spec_files.values()
        ),
        "shadow_hosts": dict(sorted(shadow_hosts.items())),
        "shadow_paths": [
            {"host": host, "path": path, "count": count}
            for (host, path), count in sorted(
                shadow_paths.items(), key=lambda item: -item[1]
            )
        ],
    }


def format_shadow_report(result):
    """대조 결과를 사람이 읽을 수 있는 형태로 정리 (Allure 첨부용)"""
    lines = [
        f"명세 엔드포인트 총 {result['spec_endpoint_count']}개",
        f"실제 호출 {result['total_calls']}건 (elice 백엔드 {result['backend_calls']}건)",
        "",
        f"[호스트 단위 그림자 API] {len(result['shadow_hosts'])}개",
    ]
    for host, count in result["shadow_hosts"].items():
        lines.append(f"  {count:5d}회  {host}")

    lines.append("")
    lines.append(f"[경로 단위 그림자 API] {len(result['shadow_paths'])}건")
    for item in result["shadow_paths"]:
        lines.append(f"  {item['count']:5d}회  {item['host']}{item['path']}")

    return "\n".join(lines)
