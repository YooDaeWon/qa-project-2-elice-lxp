import json
from contextlib import nullcontext
from urllib.parse import urlparse

try:
    import allure
except ImportError:  # pytest 자체 실행은 Allure 미설치 상태에서도 가능하게 유지
    allure = None


SENSITIVE_KEYS = {
    "authorization",
    "access_token",
    "refresh_token",
    "token",
    "sessionkey",
    "session_key",
    "password",
    "cookie",
    "set-cookie",
    "student_token",
    "educator_token",
    "student_a_token",
    "student_b_token",
}


def _is_sensitive_key(key):
    return str(key).strip().lower().replace("-", "_") in {
        item.replace("-", "_") for item in SENSITIVE_KEYS
    }


def sanitize(value):
    """Allure 첨부파일에서 인증정보만 제거하고 테스트 payload는 보존한다."""
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if _is_sensitive_key(key):
                result[str(key)] = "***REDACTED***"
            else:
                result[str(key)] = sanitize(child)
        return result
    if isinstance(value, (list, tuple, set)):
        return [sanitize(child) for child in value]
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    if hasattr(value, "read"):
        return f"<file:{getattr(value, 'name', 'stream')}>"
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


def _attach_json(data, name):
    if allure is None:
        return
    allure.attach(
        json.dumps(sanitize(data), ensure_ascii=False, indent=2, default=str),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


def attach_text(text, name):
    if allure is None:
        return
    allure.attach(
        str(text),
        name=name,
        attachment_type=allure.attachment_type.TEXT,
    )


def api_step(role, method, url):
    if allure is None:
        return nullcontext()
    path = urlparse(url).path or url
    return allure.step(f"API | {role} | {method.upper()} {path}")


def attach_request(role, method, url, kwargs, org=None):
    safe_headers = dict(kwargs.get("headers") or {})
    # Session Authorization 헤더 자체는 애초에 첨부하지 않는다.
    request_info = {
        "role": role,
        "method": method.upper(),
        "url": url,
        "organization": org,
        "params": kwargs.get("params"),
        "json": kwargs.get("json"),
        "form": kwargs.get("data"),
        "multipart": kwargs.get("files"),
        "headers": safe_headers,
    }
    _attach_json(request_info, "Request")


def attach_response(response):
    try:
        body = response.json()
    except ValueError:
        body = response.text[:10000]
    response_info = {
        "status_code": response.status_code,
        "elapsed_ms": round(response.elapsed.total_seconds() * 1000, 2),
        "body": body,
    }
    _attach_json(response_info, "Response")


def attach_exception(exc):
    attach_text(f"{type(exc).__name__}: {exc}", "Request Exception")


def validation_step(title):
    if allure is None:
        return nullcontext()
    return allure.step(f"검증 | {title}")
