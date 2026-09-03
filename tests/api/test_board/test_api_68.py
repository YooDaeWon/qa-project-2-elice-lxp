"""API TC68 전용 테스트 파일.

기존 test_board.py의 TC68를 1개 파일로 분리한 테스트입니다.
"""

from uuid import uuid4

import pytest

from clients.board_client import BoardClient

from config.settings import settings

from utils.assertions import (
    assert_business_rejected,
    assert_internal,
    assert_not_success,
    assert_permission_denied,
    assert_success,
    assert_validation_rejected,
)

from utils.helpers import contains_value, find_dict_by_value, find_first_value, first_list, require_values

def _find_board(client, board_id):
    data = assert_success(client.board_list(settings.ORG, settings.COURSE_ID))
    row = find_dict_by_value(data, "id", board_id)
    assert row is not None, f"board_id={board_id}를 board/list에서 찾지 못했습니다."
    return row

def _board_payload(board, new_name, **overrides):
    payload = {
        "board_id": board["id"],
        "course_id": settings.COURSE_ID,
        "name": new_name,
        "viewable_course_role": board["viewable_course_role"],
        "postable_course_role": board["postable_course_role"],
        "commentable_course_role": board["commentable_course_role"],
        "is_secret_default": board["is_secret_default"],
        "is_secret_force": board["is_secret_force"],
        "is_subscribed_default": board.get("is_subscribed_default", board.get("is_subscribed", False)),
    }
    payload.update(overrides)
    return payload

def _require_real_notice_board(educator_client):
    require_values(COURSE_ID=settings.COURSE_ID)
    client = BoardClient(educator_client)
    data = assert_success(client.board_list(settings.ORG, settings.COURSE_ID))
    boards = first_list(data)

    if not settings.NOTICE_BOARD_ID:
        restricted = [
            b for b in boards
            if isinstance(b, dict)
            and b.get("is_viewable", True)
            and int(b.get("viewable_course_role", 999)) <= 45
            and int(b.get("postable_course_role", 0)) > 45
        ]
        if not restricted:
            names = [f"{b.get('id')}:{b.get('name')}" for b in boards if isinstance(b, dict)]
            pytest.skip(
                "API 명세에는 Announcement/수강생 작성 제한 게시판 구조가 존재하지만, "
                f"현재 테스트 대상 course_id={settings.COURSE_ID}의 board/list에는 해당 게시판이 없습니다. "
                f"board_count={len(boards)}, boards={names}. TC63/TC64 사전조건 미충족."
            )

    board = find_dict_by_value(data, "id", settings.NOTICE_BOARD_ID)
    if board is None:
        pytest.skip(
            f"NOTICE_BOARD_ID={settings.NOTICE_BOARD_ID}를 현재 course_id={settings.COURSE_ID} board/list에서 찾지 못했습니다."
        )

    # TC64 사전조건: 수강생 작성 제한 공지 board_id. 일반 게시판 권한을 바꾸어 만들지 않는다.
    role = int(board.get("postable_course_role", 0))
    if role <= 45:
        pytest.skip(
            f"NOTICE_BOARD_ID={settings.NOTICE_BOARD_ID}가 실제 수강생 작성 제한 게시판이 아닙니다 "
            f"(postable_course_role={role}). 테스트를 위해 권한을 임의 변경하지 않습니다."
        )
    return board

def _article(client, article_id):
    data = assert_success(client.article_get(settings.ORG, article_id))
    row = data.get("board_article") if isinstance(data, dict) else None
    assert isinstance(row, dict)
    return row

def _article_ids(data):
    rows = first_list(data)
    return {str(row.get("id")) for row in rows if isinstance(row, dict) and row.get("id") is not None}


@pytest.mark.board
@pytest.mark.negative
@pytest.mark.destructive
def test_api_68(student_client, payloads):
    require_values(ORG=settings.ORG, BOARD_ID=settings.BOARD_ID)
    client = BoardClient(student_client)
    payload = dict(payloads["board"]["empty_content"])
    payload.update(board_id=settings.BOARD_ID, content="", title=f"pytest-tc68-empty-{uuid4().hex[:10]}")
    article_id = None
    response = client.article_edit(settings.ORG, payload)
    try:
        if response.status_code == 200:
            data = response.json()
            result = data.get("_result") if isinstance(data, dict) else None
            if isinstance(result, dict) and result.get("status_code") == 200:
                # TC 기대결과가 서비스 정책 조건부이므로 허용 정책이면 실제 빈 본문 생성까지 확인한다.
                data = assert_success(response)
                article_id = find_first_value(data, ("board_article_id",))
                assert article_id is not None
                article = _article(client, article_id)
                assert article.get("title") == payload["title"]
                assert article.get("content") == ""
            else:
                assert_validation_rejected(response)
                listing = assert_success(client.article_list(settings.ORG, settings.BOARD_ID))
                assert not contains_value(listing, payload["title"])
        else:
            assert_validation_rejected(response)
            listing = assert_success(client.article_list(settings.ORG, settings.BOARD_ID))
            assert not contains_value(listing, payload["title"])
    finally:
        if article_id:
            assert_success(client.article_delete(settings.ORG, article_id))
