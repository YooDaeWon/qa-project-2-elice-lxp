"""API TC16 전용 테스트 파일.

기존 test_course.py의 TC16를 1개 파일로 분리한 테스트입니다.
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
@pytest.mark.positive
def test_api_16(student_client):
    require_values(CLASSROOM_ID=settings.CLASSROOM_ID, STUDENT_ID=settings.STUDENT_ID)
    data = assert_success(ClassroomClient(student_client).get_student_courses(settings.STUDENT_ID, settings.CLASSROOM_ID, 0, 10))
    rows = [x for x in dicts_with_key(data, "course") if isinstance(x.get("course"), dict)]
    assert rows
    for row in rows:
        course = row["course"]
        assert course.get("id") is not None and course.get("title") not in (None, "")
        assert "course_type" in course
        assert "logo_url" in course or "image_url" in course
