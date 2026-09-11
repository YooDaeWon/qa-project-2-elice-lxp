"""JWT 토큰 조작 유틸 (API 호출 보안성 테스트 전용)

토큰·세션 카테고리(ID 10, 13, 14, 15)에서 토큰을 정교하게 변조하기 위한 헬퍼.
대상 시스템은 sessionkey 기반이라 변조된 토큰은 서버 세션 저장소에 없어 거부되지만,
TC의 원래 의도(payload 변조, alg:none 다운그레이드, 서명 변조)를 그대로 재현하기 위해
JWT 구조를 실제로 디코딩·재인코딩한다.
"""

import base64
import json


def _b64url_encode(data: dict) -> str:
    """dict를 JWT용 base64url 문자열로 인코딩 (패딩 제거)"""
    raw = json.dumps(data, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64url_decode(part: str) -> dict:
    """JWT의 base64url 파트를 dict로 디코딩"""
    padded = part + "=" * (-len(part) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def decode_payload(token: str) -> dict:
    """토큰의 payload(가운데 파트)를 dict로 디코딩한다.

    ID-10(exp 부재 검증)에서 payload에 exp 키가 있는지 확인하는 데 사용.
    """
    return _b64url_decode(token.split(".")[1])


def tamper_payload(token: str, **overrides) -> str:
    """payload의 특정 필드를 변조한 토큰을 생성한다 (서명은 원본 유지).

    ID-14: tamper_payload(token, _id=other_id, account_id=other_id)
    """
    header_b64, payload_b64, signature = token.split(".")
    payload = _b64url_decode(payload_b64)
    payload.update(overrides)
    return f"{header_b64}.{_b64url_encode(payload)}.{signature}"


def make_alg_none(token: str) -> str:
    """alg를 none으로 낮추고 서명을 제거한 토큰을 생성한다.

    ID-15: 서명 검증을 무력화하는 다운그레이드 공격 재현.
    """
    _, payload_b64, _ = token.split(".")
    none_header = _b64url_encode({"alg": "none", "typ": "JWT"})
    return f"{none_header}.{payload_b64}."


def tamper_signature(token: str) -> str:
    """서명(마지막 파트)의 뒤 4글자만 변조한 토큰을 생성한다.

    ID-13: payload는 유지하고 서명만 변조하여 위조 서명 거부 여부를 검증.
    """
    header_b64, payload_b64, signature = token.split(".")
    replacement = "AAAA" if not signature.endswith("AAAA") else "BBBB"
    tampered = signature[:-4] + replacement if len(signature) >= 4 else signature + replacement
    return f"{header_b64}.{payload_b64}.{tampered}"
