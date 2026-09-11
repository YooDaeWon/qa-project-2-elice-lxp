"""Course API 테스트 모음 (TC16~TC38).

테스트 카테고리 단위로 파일을 통합해 공통 import/helper 중복을 제거했다.
각 TC 함수명은 기존 test_api_XX 형식을 유지해 TC 추적성과 Allure 메타데이터를 보존한다.
"""

import pytest

from uuid import uuid4

from framework.api.classroom_client import ClassroomClient

from framework.api.course_client import CourseClient

from config.settings import settings

from utils.assertions import (
    assert_business_rejected,
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

import allure


# ---------------------------------------------------------------------------
# Category helpers
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# TC16 | 학습 과목 목록 조회 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "16")
@allure.label("priority", "P1")
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


# ---------------------------------------------------------------------------
# TC17 | 학습 과목 목록 조회 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "17")
@allure.label("priority", "P1")
def test_api_17(educator_client):
    require_values(CLASSROOM_ID=settings.CLASSROOM_ID)
    data = assert_success(CourseClient(educator_client).classroom_course_list(settings.CLASSROOM_ID, 0, 10))
    rows = first_list(data)
    assert rows
    for row in rows:
        for key in ("course_id", "title", "short_description", "course_type", "classroom_course_status", "classroom_course_progress_data"):
            assert key in row


# ---------------------------------------------------------------------------
# TC18 | 과목 상세 조회 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "18")
@allure.label("priority", "P1")
def test_api_18(student_client):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID)
    data = assert_success(CourseClient(student_client).course_get(settings.ORG, settings.COURSE_ID))
    course = data.get("course")
    assert isinstance(course, dict)
    assert str(course.get("id")) == str(settings.COURSE_ID)
    assert course.get("title") not in (None, "")
    assert "description" in course


# ---------------------------------------------------------------------------
# TC19 | 과목 상세 조회 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "19")
@allure.label("priority", "P1")
def test_api_19(educator_client):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID)
    data = assert_success(CourseClient(educator_client).course_get(settings.ORG, settings.COURSE_ID))
    course = data.get("course")
    assert isinstance(course, dict)
    assert str(course.get("id")) == str(settings.COURSE_ID)
    assert course.get("title") not in (None, "")
    assert "description" in course


# ---------------------------------------------------------------------------
# TC20 | 수업 목록 조회 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "20")
@allure.label("priority", "P1")
def test_api_20(student_client):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID)
    data = assert_success(CourseClient(student_client).lecture_list(settings.ORG, settings.COURSE_ID))
    rows = _lecture_records(data)
    assert rows
    for row in rows:
        assert row.get("id") is not None and row.get("title") not in (None, "")


# ---------------------------------------------------------------------------
# TC21 | 수업 목록 조회 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "21")
@allure.label("priority", "P1")
def test_api_21(educator_client):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID)
    data = assert_success(CourseClient(educator_client).lecture_list(settings.ORG, settings.COURSE_ID))
    rows = _lecture_records(data)
    assert rows
    for row in rows:
        assert row.get("id") is not None and row.get("title") not in (None, "")


# ---------------------------------------------------------------------------
# TC22 | 수업 자료 조회 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "22")
@allure.label("priority", "P1")
def test_api_22(student_client):
    require_values(ORG=settings.ORG, LECTURE_ID=settings.LECTURE_ID, LOCATOR_TYPE=settings.LOCATOR_TYPE)
    data = assert_success(CourseClient(student_client).lecture_page_list(settings.ORG, settings.LECTURE_ID, settings.LOCATOR_TYPE))
    pages = data.get("lecture_pages") if isinstance(data, dict) else None
    assert isinstance(pages, list) and pages, "사전조건(해당 수업에 등록된 자료 존재)이 충족되지 않았습니다."


# ---------------------------------------------------------------------------
# TC23 | 수업 자료 조회 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "23")
@allure.label("priority", "P1")
def test_api_23(educator_client):
    require_values(ORG=settings.ORG, LECTURE_ID=settings.LECTURE_ID, LOCATOR_TYPE=settings.LOCATOR_TYPE)
    data = assert_success(CourseClient(educator_client).lecture_page_list(settings.ORG, settings.LECTURE_ID, settings.LOCATOR_TYPE))
    pages = data.get("lecture_pages") if isinstance(data, dict) else None
    assert isinstance(pages, list) and pages


# ---------------------------------------------------------------------------
# TC24 | 과목 편집 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "24")
@allure.label("priority", "P1")
def test_api_24(educator_client, payloads):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID)
    client = CourseClient(educator_client)
    before = assert_success(client.course_get(settings.ORG, settings.COURSE_ID))
    course = before.get("course")
    assert isinstance(course, dict)
    original = course.get("title")
    changed = f"pytest-tc24-{uuid4().hex[:10]}"
    try:
        params = client.build_course_edit_params(course, {"title": changed})
        assert_success(client.course_edit(settings.ORG, params))
        after = assert_success(client.course_get(settings.ORG, settings.COURSE_ID))
        assert after["course"].get("title") == changed
    finally:
        current = assert_success(
            client.course_get(settings.ORG, settings.COURSE_ID)
        )["course"]
        restore = client.build_course_edit_params(
            current,
            {"title": original},
        )
        assert_success(client.course_edit(settings.ORG, restore))
        restored = assert_success(
            client.course_get(settings.ORG, settings.COURSE_ID)
        )["course"]
        assert restored.get("title") == original


# ---------------------------------------------------------------------------
# TC25 | 과목 편집 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.negative
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "25")
@allure.label("priority", "P0")
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


# ---------------------------------------------------------------------------
# TC26 | 신규 수업 생성 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "26")
@allure.label("priority", "P1")
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
        assert row.get("title") == payload["title"]
    finally:
        if lecture_id is not None:
            assert_success(client.lecture_delete(settings.ORG, lecture_id))


# ---------------------------------------------------------------------------
# TC27 | 신규 수업 생성 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.negative
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "27")
@allure.label("priority", "P0")
def test_api_27(student_client, payloads):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID)
    client = CourseClient(student_client)
    payload = clone_payload(payloads, "course", "lecture_create")
    payload["course_id"] = settings.COURSE_ID
    payload["title"] = f"pytest-tc27-blocked-{uuid4().hex[:10]}"
    response = client.lecture_edit(settings.ORG, payload)
    assert_business_rejected(response, context="TC27 수강생 신규 수업 생성 차단")
    listing = assert_success(client.lecture_list(settings.ORG, settings.COURSE_ID))
    assert not any(row.get("title") == payload["title"] for row in _lecture_records(listing))


# ---------------------------------------------------------------------------
# TC28 | 수업 수정 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "28")
@allure.label("priority", "P1")
def test_api_28(educator_client, payloads):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID, EDIT_LECTURE_ID=settings.EDIT_LECTURE_ID)
    client = CourseClient(educator_client)
    payload = clone_payload(payloads, "course", "lecture_update")
    payload.update(course_id=settings.COURSE_ID, lecture_id=settings.EDIT_LECTURE_ID)
    payload["title"] = f"pytest-tc28-{uuid4().hex[:10]}"
    assert_success(client.lecture_edit(settings.ORG, payload))
    row = _lecture(client, settings.EDIT_LECTURE_ID)
    assert row.get("title") == payload["title"]


# ---------------------------------------------------------------------------
# TC29 | 수업 수정 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.negative
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "29")
@allure.label("priority", "P0")
def test_api_29(student_client, educator_client, payloads):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID, BLOCK_EDIT_LECTURE_ID=settings.BLOCK_EDIT_LECTURE_ID)
    owner = CourseClient(educator_client)
    attacker = CourseClient(student_client)
    before = _lecture(owner, settings.BLOCK_EDIT_LECTURE_ID)
    original = before.get("title")
    payload = clone_payload(payloads, "course", "lecture_update")
    payload.update(course_id=settings.COURSE_ID, lecture_id=settings.BLOCK_EDIT_LECTURE_ID)
    payload["title"] = f"pytest-tc29-blocked-{uuid4().hex[:10]}"
    assert_permission_denied(attacker.lecture_edit(settings.ORG, payload))
    after = _lecture(owner, settings.BLOCK_EDIT_LECTURE_ID)
    assert after.get("title") == original


# ---------------------------------------------------------------------------
# TC30 | 수업 삭제 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "30")
@allure.label("priority", "P1")
def test_api_30(educator_client):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID, DELETE_LECTURE_ID=settings.DELETE_LECTURE_ID)
    client = CourseClient(educator_client)
    assert_success(client.lecture_delete(settings.ORG, settings.DELETE_LECTURE_ID))
    listing = assert_success(client.lecture_list(settings.ORG, settings.COURSE_ID))
    assert find_dict_by_value(listing, "id", settings.DELETE_LECTURE_ID) is None


# ---------------------------------------------------------------------------
# TC31 | 수업 삭제 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.negative
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "31")
@allure.label("priority", "P0")
def test_api_31(student_client, educator_client):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID, BLOCK_DELETE_LECTURE_ID=settings.BLOCK_DELETE_LECTURE_ID)
    attacker = CourseClient(student_client)
    owner = CourseClient(educator_client)
    assert_permission_denied(attacker.lecture_delete(settings.ORG, settings.BLOCK_DELETE_LECTURE_ID))
    assert _lecture(owner, settings.BLOCK_DELETE_LECTURE_ID) is not None


# ---------------------------------------------------------------------------
# TC32 | 수업 자료 생성 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "32")
@allure.label("priority", "P1")
def test_api_32(educator_client, payloads):
    require_values(ORG=settings.ORG, LECTURE_ID=settings.LECTURE_ID, LOCATOR_TYPE=settings.LOCATOR_TYPE)
    client = CourseClient(educator_client)
    payload = clone_payload(payloads, "course", "material_note_create")
    payload["lecture_id"] = settings.LECTURE_ID
    payload["title"] = f"pytest-tc32-{uuid4().hex[:10]}"
    page_id = None
    try:
        data = assert_success(client.material_note_edit(settings.ORG, payload))
        material_id = find_first_value(data, ("material_note_id",))
        assert material_id is not None
        page, listing = _material_page(client, material_id=material_id)
        assert page is not None
        page_id = page.get("id")
        assert contains_value(page, payload["title"])
    finally:
        if page_id is not None:
            assert_success(client.lecture_page_delete_bulk(settings.ORG, page_id))


# ---------------------------------------------------------------------------
# TC33 | 수업 자료 수정 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "33")
@allure.label("priority", "P1")
def test_api_33(educator_client, payloads):
    require_values(ORG=settings.ORG, LECTURE_ID=settings.LECTURE_ID, MATERIAL_NOTE_ID=settings.MATERIAL_NOTE_ID)
    client = CourseClient(educator_client)
    payload = clone_payload(payloads, "course", "material_note_update")
    payload.update(lecture_id=settings.LECTURE_ID, material_note_id=settings.MATERIAL_NOTE_ID, id=settings.MATERIAL_NOTE_ID)
    payload["title"] = f"pytest-tc33-{uuid4().hex[:10]}"
    data = assert_success(client.material_note_edit(settings.ORG, payload))
    returned = find_first_value(data, ("material_note_id",))
    assert str(returned) == str(settings.MATERIAL_NOTE_ID)
    page, _ = _material_page(client, material_id=settings.MATERIAL_NOTE_ID)
    assert page is not None and contains_value(page, payload["title"])


# ---------------------------------------------------------------------------
# TC34 | 수업 자료 삭제 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "34")
@allure.label("priority", "P1")
def test_api_34(educator_client):
    require_values(ORG=settings.ORG, LECTURE_ID=settings.LECTURE_ID, DELETE_LECTURE_PAGE_ID=settings.DELETE_LECTURE_PAGE_ID)
    client = CourseClient(educator_client)
    assert_success(client.lecture_page_delete_bulk(settings.ORG, settings.DELETE_LECTURE_PAGE_ID))
    page, _ = _material_page(client, page_id=settings.DELETE_LECTURE_PAGE_ID)
    assert page is None


# ---------------------------------------------------------------------------
# TC35 | 수업 자료 관리 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.negative
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "35")
@allure.label("priority", "P0")
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


# ---------------------------------------------------------------------------
# TC36 | 존재하지 않는 과목 ID 조회
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.negative
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "36")
@allure.label("priority", "P2")
def test_api_36(student_client):
    require_values(ORG=settings.ORG)
    response = CourseClient(student_client).course_get(settings.ORG, 99999)
    data = assert_business_rejected(response, context="TC36 존재하지 않는 course_id 조회 거부")
    assert not (isinstance(data, dict) and data.get("course")), (
        f"존재하지 않는 course_id인데 정상 course 데이터가 반환되었습니다. BODY={response.text[:2000]}"
    )


# ---------------------------------------------------------------------------
# TC37 | 음수 과목 ID 조회
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.negative
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "37")
@allure.label("priority", "P2")
def test_api_37(student_client):
    require_values(ORG=settings.ORG)
    response = CourseClient(student_client).course_get(settings.ORG, -1)
    data = assert_business_rejected(response, context="TC37 음수 course_id 조회 거부")
    assert not (isinstance(data, dict) and data.get("course")), (
        f"음수 course_id인데 정상 course 데이터가 반환되었습니다. BODY={response.text[:2000]}"
    )


# ---------------------------------------------------------------------------
# TC38 | 수업 생성 필수값 누락
# ---------------------------------------------------------------------------
@pytest.mark.course
@pytest.mark.negative
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "38")
@allure.label("priority", "P2")
def test_api_38(educator_client, payloads):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID)
    client = CourseClient(educator_client)
    before = assert_success(client.lecture_list(settings.ORG, settings.COURSE_ID))
    before_ids = {str(row.get("id")) for row in _lecture_records(before)}
    payload = clone_payload(payloads, "course", "lecture_create")
    payload["course_id"] = settings.COURSE_ID
    payload.pop("title", None)
    assert_business_rejected(
        client.lecture_edit(settings.ORG, payload),
        context="TC38 필수 title 누락 요청 거부",
    )
    after = assert_success(client.lecture_list(settings.ORG, settings.COURSE_ID))
    after_ids = {str(row.get("id")) for row in _lecture_records(after)}
    assert after_ids == before_ids
