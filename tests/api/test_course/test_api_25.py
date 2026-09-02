"""API TC25 전용 테스트 파일.

기존 test_course.py의 TC25를 1개 파일로 분리한 테스트입니다.
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
@pytest.mark.negative
@pytest.mark.destructive
def test_api_25(student_client, educator_client):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID)
    owner = CourseClient(educator_client)
    attacker = CourseClient(student_client)
    course = assert_success(owner.course_get(settings.ORG, settings.COURSE_ID))["course"]
    original = course.get("title")
    attempted = f"pytest-tc25-blocked-{uuid4().hex[:10]}"
    params = owner.build_course_edit_params(course, {"title": attempted})
    assert_permission_denied(attacker.course_edit(settings.ORG, params))
    after = assert_success(owner.course_get(settings.ORG, settings.COURSE_ID))["course"]
    assert after.get("title") == original
