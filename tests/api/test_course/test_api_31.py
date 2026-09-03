"""API TC31 전용 테스트 파일.

기존 test_course.py의 TC31를 1개 파일로 분리한 테스트입니다.
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
    response, row = client.lecture_find(
        settings.ORG,
        settings.COURSE_ID,
        lecture_id,
    )
    assert response is not None, "lecture/list 응답을 받지 못했습니다."
    assert_success(response)
    assert row is not None, (
        f"lecture_id={lecture_id}를 전체 lecture 목록에서 찾지 못했습니다."
    )
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
def test_api_31(student_client, educator_client):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID, BLOCK_DELETE_LECTURE_ID=settings.BLOCK_DELETE_LECTURE_ID)
    attacker = CourseClient(student_client)
    owner = CourseClient(educator_client)
    assert_permission_denied(attacker.lecture_delete(settings.ORG, settings.BLOCK_DELETE_LECTURE_ID))
    assert _lecture(owner, settings.BLOCK_DELETE_LECTURE_ID) is not None
