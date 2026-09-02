"""API TC14 전용 테스트 파일.

기존 test_classroom.py의 TC14를 1개 파일로 분리한 테스트입니다.
"""

import pytest

from uuid import uuid4

from clients.classroom_client import ClassroomClient

from clients.course_client import CourseClient

from config.settings import settings

from utils.assertions import assert_permission_denied, assert_success, json_body

from utils.helpers import (
    contains_value,
    dicts_with_key,
    first_list,
    require_values,
)

def _course_rows(data):
    return [row for row in dicts_with_key(data, "course") if isinstance(row.get("course"), dict)]

def _assert_course_card(row, with_stats=False):
    course = row["course"]
    assert course.get("id") is not None
    assert course.get("title") not in (None, "")
    assert "logo_url" in course or "image_url" in course
    if with_stats:
        for key in ("learning_progress", "practice_score", "test_score"):
            assert key in row

def _numeric_value(value, field_name, *, allow_none=False):
    if value is None:
        assert allow_none, f"{field_name}가 null입니다."
        return None

    try:
        number = float(str(value))
    except (TypeError, ValueError):
        raise AssertionError(
            f"{field_name}는 숫자 또는 허용된 null이어야 합니다. actual={value!r}"
        )

    assert 0 <= number <= 100, (
        f"{field_name}는 0~100 범위여야 합니다. actual={number}"
    )
    return number

def _student_rows(data):
    return [row for row in dicts_with_key(data, "account") if isinstance(row.get("account"), dict)]

def _account_ids(data):
    ids = set()

    def walk(value):
        if isinstance(value, dict):
            account = value.get("account")
            if isinstance(account, dict) and account.get("id") not in (None, ""):
                ids.add(str(account.get("id")))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    return ids

def _assert_schedule_preview(client):
    summary = assert_success(
        client.get_schedule_summary(
            settings.CLASSROOM_ID,
            settings.DATE_START,
            settings.DATE_END,
        )
    )
    days = summary.get("days")
    assert isinstance(days, list) and days

    for day in days:
        assert isinstance(day, dict)
        assert "date" in day
        assert "schedule_exists" in day

    scheduled = next(
        (day for day in days if day.get("schedule_exists")),
        None,
    )
    assert scheduled is not None, (
        "사전조건(조회 기간 내 등록된 일정 존재)이 충족되지 않았습니다."
    )

    by_date = assert_success(
        client.get_schedule_by_date(
            settings.CLASSROOM_ID,
            scheduled["date"],
        )
    )

    # 실제 /schedule/by_date 응답은 날짜 그룹의 list이다.
    assert isinstance(by_date, list), (
        "GET /schedule/by_date 응답이 list가 아닙니다. "
        f"실제 타입={type(by_date).__name__}"
    )
    assert by_date, "GET /schedule/by_date 응답 목록이 비어 있습니다."

    date_group = next(
        (
            row for row in by_date
            if isinstance(row, dict)
            and str(row.get("date")) == str(scheduled["date"])
        ),
        None,
    )
    assert date_group is not None, (
        f"summary에서 일정이 있다고 표시된 날짜 "
        f"{scheduled['date']}가 by_date 응답에 없습니다."
    )

    assert "relative_date" in date_group
    schedules = date_group.get("schedules")
    assert isinstance(schedules, list)
    assert schedules, (
        f"{scheduled['date']}의 schedule_exists=true인데 "
        "by_date.schedules가 비어 있습니다."
    )

    for schedule in schedules:
        assert isinstance(schedule, dict)
        for key in ("summary", "dt_start", "dt_end"):
            assert key in schedule
        # is_live_lecture는 명세/TC에서 확인 대상. 응답에 포함되는지 검사한다.
        assert "is_live_lecture" in schedule

def _assert_article_preview(data, expected_count):
    rows = first_list(data)
    assert len(rows) == expected_count
    for row in rows:
        for key in ("id", "title", "user", "content", "is_secret", "created"):
            assert key in row


@pytest.mark.classroom
@pytest.mark.positive
def test_api_14(educator_client):
    """
    TC14 - 클래스 학습현황 요약 데이터 조회 (교육자)

    UI 비교를 제거하고 API 기능 테스트 범위로 공식 수정한다.

    검증 항목
    1. 교육자 토큰으로 dashboard /course 조회 성공
    2. course.id / course.title 정상 반환
    3. learning_progress는 0~100 숫자
    4. practice_score / test_score는 0~100 숫자 또는 데이터가 없을 경우 null
    5. dashboard 응답의 course.id가 실제 classroom 과목 목록 범위에 포함되는지 교차 검증
    """
    require_values(CLASSROOM_ID=settings.CLASSROOM_ID)

    dashboard_data = assert_success(
        ClassroomClient(educator_client).get_dashboard_courses(
            settings.CLASSROOM_ID,
            0,
            3,
        )
    )
    rows = _course_rows(dashboard_data)
    assert rows, "dashboard /course 응답에 과목 데이터가 없습니다."

    dashboard_course_ids = set()

    for row in rows:
        _assert_course_card(row, with_stats=True)

        course = row["course"]
        course_id = str(course["id"])
        dashboard_course_ids.add(course_id)

        _numeric_value(
            row.get("learning_progress"),
            f"course_id={course_id}.learning_progress",
            allow_none=False,
        )
        _numeric_value(
            row.get("practice_score"),
            f"course_id={course_id}.practice_score",
            allow_none=True,
        )
        _numeric_value(
            row.get("test_score"),
            f"course_id={course_id}.test_score",
            allow_none=True,
        )

    # dashboard의 classroom_id 필터가 실제 해당 클래스의 과목 범위를 반환하는지
    # classroom 서비스 과목 목록과 course_id를 교차 검증한다.
    classroom_data = assert_success(
        CourseClient(educator_client).classroom_course_list(
            settings.CLASSROOM_ID,
            0,
            100,
        )
    )
    classroom_rows = first_list(classroom_data)
    assert classroom_rows, "classroom 과목 목록이 비어 있습니다."

    classroom_course_ids = {
        str(item.get("course_id"))
        for item in classroom_rows
        if isinstance(item, dict) and item.get("course_id") not in (None, "")
    }
    assert classroom_course_ids, "classroom 과목 목록에서 course_id를 확인하지 못했습니다."

    unexpected = dashboard_course_ids - classroom_course_ids
    assert not unexpected, (
        "dashboard /course 응답에 현재 classroom_id 범위 밖의 과목이 포함되었습니다: "
        f"{sorted(unexpected)}"
    )
