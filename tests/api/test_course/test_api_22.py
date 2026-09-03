"""API TC22 전용 테스트 파일.

기존 test_course.py의 TC22를 1개 파일로 분리한 테스트입니다.
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
def test_api_22(student_client):
    require_values(ORG=settings.ORG, LECTURE_ID=settings.LECTURE_ID, LOCATOR_TYPE=settings.LOCATOR_TYPE)
    data = assert_success(CourseClient(student_client).lecture_page_list(settings.ORG, settings.LECTURE_ID, settings.LOCATOR_TYPE))
    pages = data.get("lecture_pages") if isinstance(data, dict) else None
    assert isinstance(pages, list) and pages, "사전조건(해당 수업에 등록된 자료 존재)이 충족되지 않았습니다."
