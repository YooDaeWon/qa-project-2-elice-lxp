from copy import deepcopy
from typing import Any, Iterable

import pytest


def require_values(**values):
    missing = [name for name, value in values.items() if value in (None, "")]
    if missing:
        pytest.skip(
            "필수 .env 값이 설정되지 않았습니다: " + ", ".join(missing)
        )
    return values


def clone_payload(payloads, group: str, name: str) -> dict:
    payload = payloads.get(group, {}).get(name)
    if not payload:
        pytest.skip(
            f"data/payloads/{group}.json의 '{name}' payload를 입력하세요."
        )
    return deepcopy(payload)


def walk_json(data: Any):
    if isinstance(data, dict):
        yield data
        for value in data.values():
            yield from walk_json(value)
    elif isinstance(data, list):
        for item in data:
            yield from walk_json(item)


def recursive_keys(data: Any) -> set:
    keys = set()
    for node in walk_json(data):
        if isinstance(node, dict):
            keys.update(node.keys())
    return keys


def has_keys_anywhere(data: Any, *keys: str) -> bool:
    all_keys = recursive_keys(data)
    return all(key in all_keys for key in keys)


def contains_value(data: Any, expected: Any) -> bool:
    if isinstance(data, dict):
        return any(contains_value(v, expected) for v in data.values())
    if isinstance(data, list):
        return any(contains_value(v, expected) for v in data)

    return str(data) == str(expected)


def find_first_value(data: Any, keys: Iterable[str]):
    wanted = set(keys)

    if isinstance(data, dict):
        for key, value in data.items():
            if key in wanted and value not in (None, ""):
                return value

        for value in data.values():
            found = find_first_value(value, wanted)
            if found not in (None, ""):
                return found

    elif isinstance(data, list):
        for item in data:
            found = find_first_value(item, wanted)
            if found not in (None, ""):
                return found

    return None


def first_list(data: Any):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # 자주 쓰이는 목록 필드 우선
        for key in (
            "results",
            "items",
            "courses",
            "students",
            "schedules",
            "articles",
            "board_articles",
            "lecture_pages",
            "boards",
            "lectures",
            "data",
        ):
            value = data.get(key)
            if isinstance(value, list):
                return value

        for value in data.values():
            found = first_list(value)
            if isinstance(found, list):
                return found

    return []


def scalar_payload_values(payload: dict):
    for key, value in payload.items():
        if isinstance(value, (str, int, float, bool)) and value not in ("", None):
            yield key, value


def response_contains_payload_values(data: Any, payload: dict, ignore_keys=None):
    ignore_keys = set(ignore_keys or [])

    checked = 0
    for key, value in scalar_payload_values(payload):
        if key in ignore_keys:
            continue
        checked += 1
        if not contains_value(data, value):
            return False

    return checked > 0



def dicts_with_key(data: Any, key: str):
    return [node for node in walk_json(data) if isinstance(node, dict) and key in node]


def find_dict_by_value(data: Any, key: str, value: Any):
    for node in walk_json(data):
        if isinstance(node, dict) and str(node.get(key)) == str(value):
            return node
    return None


def all_values_for_key(data: Any, key: str):
    values = []
    for node in walk_json(data):
        if isinstance(node, dict) and key in node:
            values.append(node[key])
    return values
