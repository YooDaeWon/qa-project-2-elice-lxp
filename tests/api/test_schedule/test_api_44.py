"""API TC44 전용 테스트 파일.

기존 test_schedule.py의 TC44를 1개 파일로 분리한 테스트입니다.
"""

from datetime import datetime, timedelta, timezone

from uuid import uuid4

import pytest

from clients.schedule_client import ScheduleClient

from config.settings import settings

from utils.assertions import (
    assert_not_success,
    assert_permission_denied,
    assert_success,
    assert_validation_rejected,
)

from utils.helpers import contains_value, find_first_value, first_list, require_values

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


@pytest.mark.schedule
@pytest.mark.negative
@pytest.mark.destructive
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
