"""Schedule API 테스트 모음 (TC39~TC51).

테스트 카테고리 단위로 파일을 통합해 공통 import/helper 중복을 제거했다.
각 TC 함수명은 기존 test_api_XX 형식을 유지해 TC 추적성과 Allure 메타데이터를 보존한다.
"""

from datetime import datetime, timedelta, timezone

from uuid import uuid4

import pytest

from framework.api.schedule_client import ScheduleClient

from config.settings import settings

from utils.assertions import (
    assert_not_success,
    assert_permission_denied,
    assert_success,
    assert_validation_rejected,
)

from utils.helpers import contains_value, find_first_value, first_list, require_values

import allure


# ---------------------------------------------------------------------------
# Category helpers
# ---------------------------------------------------------------------------
def _require_range():
    require_values(CLASSROOM_ID=settings.CLASSROOM_ID, DATE_START=settings.DATE_START, DATE_END=settings.DATE_END)


def _future_payload(summary, start_hour=10, invalid=False, live=False):
    kst = timezone(timedelta(hours=9))
    day = datetime.now(kst).replace(hour=start_hour, minute=0, second=0, microsecond=0) + timedelta(days=1)
    end = day - timedelta(hours=1) if invalid else day + timedelta(hours=1)
    payload = {
        "classroom_id": settings.CLASSROOM_ID,
        "summary": summary,
        "dt_start": day.isoformat(),
        "dt_end": end.isoformat(),
    }
    if live:
        payload.update(course_id=int(settings.COURSE_ID), enable_lectureroom=True)
    return payload


def _payload_query_window(payload, padding_hours=2):
    """생성/생성시도 payload의 실제 날짜를 포함하는 재조회 범위를 만든다."""
    start = ScheduleClient._parse_datetime(payload["dt_start"])
    end = ScheduleClient._parse_datetime(payload["dt_end"])
    assert start is not None and end is not None
    low = min(start, end) - timedelta(hours=padding_hours)
    high = max(start, end) + timedelta(hours=padding_hours)
    return low.isoformat(), high.isoformat()


def _assert_schedule_rows(data):
    rows = first_list(data)
    assert isinstance(rows, list)
    for row in rows:
        for key in ("id", "summary", "dt_start", "dt_end"):
            assert key in row
    return rows


def _find_schedule_by_summary(data, summary):
    """GET /schedule 응답에서 이번 테스트가 생성한 고유 summary의 일정만 찾는다."""
    def walk(value):
        if isinstance(value, dict):
            if value.get("summary") == summary and value.get("id") not in (None, ""):
                return value
            for child in value.values():
                found = walk(child)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = walk(child)
                if found is not None:
                    return found
        return None

    return walk(data)


# ---------------------------------------------------------------------------
# TC39 | 월간 일정 조회 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "39")
@allure.label("priority", "P1")
def test_api_39(student_client):
    _require_range()
    data = assert_success(ScheduleClient(student_client).list_schedules(settings.CLASSROOM_ID, settings.DATE_START, settings.DATE_END, settings.SCHEDULE_COUNT))
    _assert_schedule_rows(data)


# ---------------------------------------------------------------------------
# TC40 | 월간 일정 조회 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "40")
@allure.label("priority", "P1")
def test_api_40(educator_client):
    _require_range()
    data = assert_success(ScheduleClient(educator_client).list_schedules(settings.CLASSROOM_ID, settings.DATE_START, settings.DATE_END, settings.SCHEDULE_COUNT))
    _assert_schedule_rows(data)


# ---------------------------------------------------------------------------
# TC41 | 신규 일정 생성 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "41")
@allure.label("priority", "P1")
def test_api_41(educator_client):
    _require_range()
    client = ScheduleClient(educator_client)
    payload = _future_payload(f"pytest-tc41-{uuid4().hex[:10]}", 10)
    schedule_id = None
    try:
        data = assert_success(client.create_schedule(payload))
        schedule_id = find_first_value(data, ("schedule_id", "id"))

        query_start, query_end = _payload_query_window(payload)
        listing = assert_success(
            client.list_schedules(
                settings.CLASSROOM_ID,
                query_start,
                query_end,
                settings.SCHEDULE_COUNT,
            )
        )
        created = _find_schedule_by_summary(listing, payload["summary"])
        assert created is not None, "생성한 일정이 재조회 결과에서 확인되지 않았습니다."

        # POST 응답에 id가 없는 구현도 있으므로 TC의 재조회 결과에서 정확한 id를 확보한다.
        schedule_id = schedule_id or created.get("id")
        assert schedule_id not in (None, "")
    finally:
        if schedule_id:
            assert_success(
                client.delete_schedule(
                    schedule_id,
                    settings.CLASSROOM_ID,
                )
            )


# ---------------------------------------------------------------------------
# TC42 | 신규 일정 생성 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.negative
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "42")
@allure.label("priority", "P0")
def test_api_42(student_client):
    _require_range()
    client = ScheduleClient(student_client)
    payload = _future_payload(f"pytest-tc42-blocked-{uuid4().hex[:10]}", 11)
    assert_permission_denied(client.create_schedule(payload), allow_internal_409=True)
    query_start, query_end = _payload_query_window(payload)
    listing = assert_success(client.list_schedules(settings.CLASSROOM_ID, query_start, query_end, settings.SCHEDULE_COUNT))
    assert not contains_value(listing, payload["summary"])


# ---------------------------------------------------------------------------
# TC43 | 일정 수정 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "43")
@allure.label("priority", "P1")
def test_api_43(educator_client):
    require_values(CLASSROOM_ID=settings.CLASSROOM_ID, SCHEDULE_ID=settings.SCHEDULE_ID)
    client = ScheduleClient(educator_client)
    changed = f"pytest-tc43-{uuid4().hex[:10]}"
    assert_success(client.patch_schedule(settings.SCHEDULE_ID, {"classroom_id": settings.CLASSROOM_ID, "summary": changed}))
    after = assert_success(client.get_schedule(settings.SCHEDULE_ID, settings.CLASSROOM_ID))
    assert after.get("summary") == changed


# ---------------------------------------------------------------------------
# TC44 | 일정 수정 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.negative
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "44")
@allure.label("priority", "P0")
def test_api_44(student_client, educator_client):
    require_values(CLASSROOM_ID=settings.CLASSROOM_ID, BLOCK_UPDATE_SCHEDULE_ID=settings.BLOCK_UPDATE_SCHEDULE_ID)
    owner = ScheduleClient(educator_client)
    attacker = ScheduleClient(student_client)
    before = assert_success(owner.get_schedule(settings.BLOCK_UPDATE_SCHEDULE_ID, settings.CLASSROOM_ID))
    original = before.get("summary")
    attempted = f"pytest-tc44-blocked-{uuid4().hex[:10]}"
    assert_permission_denied(attacker.patch_schedule(settings.BLOCK_UPDATE_SCHEDULE_ID, {"classroom_id": settings.CLASSROOM_ID, "summary": attempted}))
    after = assert_success(owner.get_schedule(settings.BLOCK_UPDATE_SCHEDULE_ID, settings.CLASSROOM_ID))
    assert after.get("summary") == original


# ---------------------------------------------------------------------------
# TC45 | 일정 삭제 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "45")
@allure.label("priority", "P1")
def test_api_45(educator_client):
    require_values(CLASSROOM_ID=settings.CLASSROOM_ID, DELETE_SCHEDULE_ID=settings.DELETE_SCHEDULE_ID)
    client = ScheduleClient(educator_client)
    assert_success(client.delete_schedule(settings.DELETE_SCHEDULE_ID, settings.CLASSROOM_ID))
    assert_not_success(client.get_schedule(settings.DELETE_SCHEDULE_ID, settings.CLASSROOM_ID))


# ---------------------------------------------------------------------------
# TC46 | 일정 삭제 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.negative
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "46")
@allure.label("priority", "P0")
def test_api_46(student_client, educator_client):
    require_values(CLASSROOM_ID=settings.CLASSROOM_ID, BLOCK_DELETE_SCHEDULE_ID=settings.BLOCK_DELETE_SCHEDULE_ID)
    attacker = ScheduleClient(student_client)
    owner = ScheduleClient(educator_client)
    assert_permission_denied(attacker.delete_schedule(settings.BLOCK_DELETE_SCHEDULE_ID, settings.CLASSROOM_ID))
    data = assert_success(owner.get_schedule(settings.BLOCK_DELETE_SCHEDULE_ID, settings.CLASSROOM_ID))
    assert str(data.get("id")) == str(settings.BLOCK_DELETE_SCHEDULE_ID)


# ---------------------------------------------------------------------------
# TC47 | 잘못된 일정 날짜 범위
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.negative
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "47")
@allure.label("priority", "P2")
def test_api_47(educator_client):
    _require_range()
    client = ScheduleClient(educator_client)
    payload = _future_payload(f"pytest-tc47-invalid-{uuid4().hex[:10]}", 12, invalid=True)
    response = client.create_schedule(payload)
    assert_validation_rejected(response, allowed_http=(409, 422), allowed_internal=(409, 422))
    query_start, query_end = _payload_query_window(payload)
    listing = assert_success(client.list_schedules(settings.CLASSROOM_ID, query_start, query_end, settings.SCHEDULE_COUNT))
    assert not contains_value(listing, payload["summary"])


# ---------------------------------------------------------------------------
# TC48 | 라이브 강의 일정 생성 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "48")
@allure.label("priority", "P1")
def test_api_48(educator_client):
    _require_range(); require_values(COURSE_ID=settings.COURSE_ID)
    client = ScheduleClient(educator_client)
    payload = _future_payload(f"pytest-tc48-live-{uuid4().hex[:10]}", 13, live=True)
    schedule_id = None
    try:
        data = assert_success(client.create_schedule(payload))
        schedule_id = find_first_value(data, ("schedule_id", "id"))

        query_start, query_end = _payload_query_window(payload)
        listing = assert_success(
            client.list_schedules(
                settings.CLASSROOM_ID,
                query_start,
                query_end,
                settings.SCHEDULE_COUNT,
            )
        )
        created = _find_schedule_by_summary(listing, payload["summary"])
        assert created is not None, "생성한 라이브 일정이 재조회 결과에서 확인되지 않았습니다."

        schedule_id = schedule_id or created.get("id")
        assert schedule_id not in (None, "")

        detail = assert_success(
            client.get_schedule(
                schedule_id,
                settings.CLASSROOM_ID,
            )
        )
        lectureroom_id = find_first_value(
            detail,
            ("lectureroom_id", "lecture_room_id", "lectureroomId"),
        )

        # '응답 안의 아무 True 값'이 아니라 라이브 강의실을 의미하는 필드만 검증한다.
        assert (
            detail.get("enable_lectureroom") is True
            or detail.get("is_live_lecture") is True
            or lectureroom_id not in (None, "")
        ), "생성된 일정에서 라이브 강의실 활성화 상태를 확인할 수 없습니다."
    finally:
        if schedule_id:
            assert_success(
                client.delete_schedule(
                    schedule_id,
                    settings.CLASSROOM_ID,
                )
            )


# ---------------------------------------------------------------------------
# TC49 | 라이브 강의 일정 생성 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.negative
@pytest.mark.destructive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "49")
@allure.label("priority", "P0")
def test_api_49(student_client):
    _require_range(); require_values(COURSE_ID=settings.COURSE_ID)
    client = ScheduleClient(student_client)
    payload = _future_payload(f"pytest-tc49-live-blocked-{uuid4().hex[:10]}", 14, live=True)
    assert_permission_denied(client.create_schedule(payload))
    query_start, query_end = _payload_query_window(payload)
    listing = assert_success(client.list_schedules(settings.CLASSROOM_ID, query_start, query_end, settings.SCHEDULE_COUNT))
    assert not contains_value(listing, payload["summary"])


# ---------------------------------------------------------------------------
# TC50 | 라이브 강의실 참여 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "50")
@allure.label("priority", "P1")
def test_api_50(student_client):
    require_values(ORG=settings.ORG, LECTUREROOM_ID=settings.LECTUREROOM_ID)
    data = assert_success(ScheduleClient(student_client).join_lectureroom(settings.ORG, settings.LECTUREROOM_ID, 0))
    assert data.get("access_token") not in (None, "")
    assert data.get("lectureroom_join_id") not in (None, "")


# ---------------------------------------------------------------------------
# TC51 | 라이브 강의실 참여 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.schedule
@pytest.mark.positive
@allure.label("owner", "parkseongbin")
@allure.label("team", "QA4")
@allure.label("tc_id", "51")
@allure.label("priority", "P1")
def test_api_51(educator_client):
    require_values(ORG=settings.ORG, LECTUREROOM_ID=settings.LECTUREROOM_ID)
    data = assert_success(ScheduleClient(educator_client).join_lectureroom(settings.ORG, settings.LECTUREROOM_ID, 10))
    assert data.get("access_token") not in (None, "")
    assert data.get("lectureroom_join_id") not in (None, "")
