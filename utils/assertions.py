from typing import Any

from utils.helpers import has_keys_anywhere
from utils.allure_report import validation_step


def json_body(response):
    try:
        return response.json()
    except ValueError as exc:
        raise AssertionError(
            f"JSON 응답이 아닙니다. HTTP={response.status_code}, BODY={response.text[:1000]}"
        ) from exc


def internal_result(data: Any):
    if isinstance(data, dict) and isinstance(data.get("_result"), dict):
        return data["_result"]
    return None


def internal_status_code(data: Any):
    result = internal_result(data)
    return result.get("status_code") if result else None


def assert_http(response, expected=200):
    expected = (expected,) if isinstance(expected, int) else tuple(expected)
    with validation_step(f"HTTP status | expected={expected} / actual={response.status_code}"):
        assert response.status_code in expected, (
            f"예상 HTTP={expected}, 실제 HTTP={response.status_code}\nBODY={response.text[:2000]}"
        )
    return response


def assert_success(response):
    """HTTP 200 + legacy _result가 있으면 내부 200/status ok까지 검증."""
    assert_http(response, 200)
    data = json_body(response)
    result = internal_result(data)
    if result is not None:
        with validation_step(
            f"Legacy success | status_code=200/status=ok / actual={result.get('status_code')}/{result.get('status')}"
        ):
            assert result.get("status_code") == 200, (
                f"예상 내부 status_code=200, 실제={result.get('status_code')}\nBODY={response.text[:2000]}"
            )
            assert result.get("status") == "ok", (
                f"예상 내부 status=ok, 실제={result.get('status')}\nBODY={response.text[:2000]}"
            )
    return data


def assert_internal(response, expected_code, expected_status=None, expected_fail_code=None):
    assert_http(response, 200)
    data = json_body(response)
    result = internal_result(data)
    assert result is not None, f"_result가 응답에 없습니다.\nBODY={response.text[:2000]}"
    with validation_step(
        f"Internal status_code | expected={expected_code} / actual={result.get('status_code')}"
    ):
        assert result.get("status_code") == expected_code, (
            f"예상 내부 status_code={expected_code}, 실제={result.get('status_code')}\nBODY={response.text[:2000]}"
        )
    if expected_status is not None:
        assert result.get("status") == expected_status, (
            f"예상 내부 status={expected_status}, 실제={result.get('status')}\nBODY={response.text[:2000]}"
        )
    if expected_fail_code is not None:
        assert data.get("fail_code") == expected_fail_code, (
            f"예상 fail_code={expected_fail_code}, 실제={data.get('fail_code')}\nBODY={response.text[:2000]}"
        )
    return data


def _response_data_or_text(response):
    try:
        return response.json()
    except ValueError:
        return {"_raw_text": response.text[:2000]}

def is_business_rejected(response):
    http = response.status_code
    if 400 <= http < 500:
        return True
    if http != 200:
        return False
    try:
        data = response.json()
    except ValueError:
        return False
    result = internal_result(data)
    if not result:
        return False
    code = result.get("status_code")
    status = str(result.get("status", "")).lower()
    return isinstance(code, int) and 400 <= code < 500 and status != "ok"

def rejection_summary(response):
    data = _response_data_or_text(response)
    result = internal_result(data)
    return {
        "http_status": response.status_code,
        "internal_status": result.get("status") if result else None,
        "internal_status_code": result.get("status_code") if result else None,
        "fail_code": data.get("fail_code") if isinstance(data, dict) else None,
        "reason": result.get("reason") if result else None,
    }

def assert_business_rejected(response, *, context="요청 거부"):
    summary = rejection_summary(response)
    with validation_step(f"{context} | expected=business rejection / actual={summary}"):
        assert is_business_rejected(response), (
            f"{context}이 기대되지만 정상적인 business rejection이 아닙니다.\n"
            f"ACTUAL={summary}\nBODY={response.text[:2000]}"
        )
    return _response_data_or_text(response)

def assert_permission_denied(response, **_kwargs):
    return assert_business_rejected(response, context="권한 없는 요청 차단")

def assert_validation_rejected(response, **_kwargs):
    return assert_business_rejected(response, context="유효하지 않은 요청 차단")

def assert_denied(response, **_kwargs):
    return assert_business_rejected(response, context="요청 차단")

def assert_not_success(response):
    return assert_business_rejected(response, context="성공하지 않아야 하는 요청")

def assert_fields(data, *fields):
    assert has_keys_anywhere(data, *fields), (
        f"응답에서 필요한 필드를 찾지 못했습니다: {fields}\n응답={str(data)[:2000]}"
    )
