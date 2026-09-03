"""API TC35 전용 테스트 파일.

기존 test_course.py의 TC35를 1개 파일로 분리한 테스트입니다.
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
def test_api_35(student_client, educator_client, payloads):
    require_values(
        ORG=settings.ORG, LECTURE_ID=settings.LECTURE_ID,
        BLOCK_MATERIAL_NOTE_ID=settings.BLOCK_MATERIAL_NOTE_ID,
        BLOCK_DELETE_LECTURE_PAGE_ID=settings.BLOCK_DELETE_LECTURE_PAGE_ID,
    )
    attacker = CourseClient(student_client)
    owner = CourseClient(educator_client)
    before_page, _ = _material_page(owner, material_id=settings.BLOCK_MATERIAL_NOTE_ID)
    assert before_page is not None
    before_title = before_page.get("title")

    create_payload = clone_payload(payloads, "course", "material_note_create")
    create_payload["lecture_id"] = settings.LECTURE_ID
    create_payload["title"] = f"pytest-tc35-create-blocked-{uuid4().hex[:10]}"
    assert_permission_denied(attacker.material_note_edit(settings.ORG, create_payload))

    update_payload = clone_payload(payloads, "course", "material_note_update")
    update_payload.update(
        lecture_id=settings.LECTURE_ID,
        material_note_id=settings.BLOCK_MATERIAL_NOTE_ID,
        id=settings.BLOCK_MATERIAL_NOTE_ID,
    )
    update_payload["title"] = f"pytest-tc35-update-blocked-{uuid4().hex[:10]}"
    assert_permission_denied(attacker.material_note_edit(settings.ORG, update_payload))
    assert_permission_denied(attacker.lecture_page_delete_bulk(settings.ORG, settings.BLOCK_DELETE_LECTURE_PAGE_ID))

    after_page, after_data = _material_page(owner, material_id=settings.BLOCK_MATERIAL_NOTE_ID)
    assert after_page is not None
    assert after_page.get("title") == before_title
    assert find_dict_by_value(after_data, "id", settings.BLOCK_DELETE_LECTURE_PAGE_ID) is not None
    assert not contains_value(after_data, create_payload["title"])
