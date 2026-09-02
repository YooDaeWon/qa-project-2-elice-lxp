"""API TC26 전용 테스트 파일.

기존 test_course.py의 TC26를 1개 파일로 분리한 테스트입니다.
"""

import pytest

from uuid import uuid4

from clients.classroom_client import ClassroomClient

from clients.course_client import CourseClient

from config.settings import settings

from utils.assertions import (
    assert_business_rejected,
    assert_internal,
    assert_not_success,
    assert_permission_denied,
    assert_success,
)

from utils.helpers import (
    clone_payload,
    contains_value,
    dicts_with_key,
    find_dict_by_value,
    find_first_value,
    first_list,
    require_values,
)

def _lecture_records(data):
    records = data.get("lectures", []) if isinstance(data, dict) else []
    return records if isinstance(records, list) else []

def _lecture(client, lecture_id):
    data = assert_success(client.lecture_list(settings.ORG, settings.COURSE_ID))
    row = find_dict_by_value(data, "id", lecture_id)
    assert row is not None, f"lecture_id={lecture_id}를 목록에서 찾지 못했습니다."
    return row

def _material_page(client, page_id=None, material_id=None):
    data = assert_success(client.lecture_page_list(settings.ORG, settings.LECTURE_ID, settings.LOCATOR_TYPE))
    if page_id is not None:
        return find_dict_by_value(data, "id", page_id), data
    if material_id is not None:
        return find_dict_by_value(data, "material_id", material_id), data
    return None, data


@pytest.mark.course
@pytest.mark.destructive
def test_api_26(educator_client, payloads):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID)
    client = CourseClient(educator_client)
    payload = clone_payload(payloads, "course", "lecture_create")
    payload["course_id"] = settings.COURSE_ID
    payload["title"] = f"pytest-tc26-{uuid4().hex[:10]}"
    lecture_id = None
    try:
        data = assert_success(client.lecture_edit(settings.ORG, payload))
        lecture_id = find_first_value(data, ("lecture_id",))
        assert lecture_id is not None
        listing = assert_success(client.lecture_list(settings.ORG, settings.COURSE_ID))
        row = find_dict_by_value(listing, "id", lecture_id)
        assert row is not None and row.get("title") == payload["title"]
    finally:
        if lecture_id is not None:
            assert_success(client.lecture_delete(settings.ORG, lecture_id))
