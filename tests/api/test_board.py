"""Board API 테스트 모음 (TC52~TC68).

테스트 카테고리 단위로 파일을 통합해 공통 import/helper 중복을 제거했다.
각 TC 함수명은 기존 test_api_XX 형식을 유지해 TC 추적성과 Allure 메타데이터를 보존한다.
"""

from uuid import uuid4

import pytest

from clients.board_client import BoardClient

from config.settings import settings

from utils.assertions import (
    assert_business_rejected,
    assert_not_success,
    assert_permission_denied,
    assert_success,
    assert_validation_rejected,
)

from utils.helpers import contains_value, find_dict_by_value, find_first_value, first_list, require_values


# ---------------------------------------------------------------------------
# Category helpers
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# TC52 | 게시글 목록 조회 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.positive
def test_api_52(student_client):
    require_values(CLASSROOM_ID=settings.CLASSROOM_ID)
    data = assert_success(BoardClient(student_client).classroom_articles(settings.CLASSROOM_ID, "created_desc", 0, 10))
    rows = first_list(data)
    assert rows
    for row in rows:
        for key in ("id", "title", "user", "is_secret", "created"):
            assert key in row


# ---------------------------------------------------------------------------
# TC53 | 게시글 목록 조회 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.positive
def test_api_53(educator_client):
    require_values(CLASSROOM_ID=settings.CLASSROOM_ID)
    data = assert_success(BoardClient(educator_client).classroom_articles(settings.CLASSROOM_ID, "created_desc", 0, 10))
    rows = first_list(data)
    assert rows
    for row in rows:
        for key in ("id", "title", "user", "is_secret", "created"):
            assert key in row


# ---------------------------------------------------------------------------
# TC54 | 게시글 상세 조회 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.positive
def test_api_54(student_client):
    require_values(ORG=settings.ORG, BOARD_ARTICLE_ID=settings.BOARD_ARTICLE_ID)
    article = _article(BoardClient(student_client), settings.BOARD_ARTICLE_ID)
    assert str(article.get("id")) == str(settings.BOARD_ARTICLE_ID)
    for key in ("title", "content", "author"):
        assert key in article or (key == "author" and "user" in article)


# ---------------------------------------------------------------------------
# TC55 | 게시글 상세 조회 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.positive
def test_api_55(educator_client):
    require_values(ORG=settings.ORG, BOARD_ARTICLE_ID=settings.BOARD_ARTICLE_ID)
    article = _article(BoardClient(educator_client), settings.BOARD_ARTICLE_ID)
    assert str(article.get("id")) == str(settings.BOARD_ARTICLE_ID)
    assert article.get("title") not in (None, "") and "content" in article


# ---------------------------------------------------------------------------
# TC56 | 일반 게시글 생성 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.destructive
def test_api_56(student_client, payloads):
    require_values(ORG=settings.ORG, BOARD_ID=settings.BOARD_ID)
    client = BoardClient(student_client)
    payload = dict(payloads["board"]["article_create"])
    payload.update(board_id=settings.BOARD_ID, is_secret=False, title=f"pytest-tc56-{uuid4().hex[:10]}")
    article_id = None
    try:
        data = assert_success(client.article_edit(settings.ORG, payload))
        article_id = find_first_value(data, ("board_article_id",))
        assert article_id is not None
        listing = assert_success(client.article_list(settings.ORG, settings.BOARD_ID))
        assert str(article_id) in _article_ids(listing)
        article = _article(client, article_id)
        assert article.get("title") == payload["title"] and article.get("is_secret") is False
    finally:
        if article_id:
            assert_success(client.article_delete(settings.ORG, article_id))


# ---------------------------------------------------------------------------
# TC57 | 비밀글 생성 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.destructive
def test_api_57(student_client, payloads):
    require_values(ORG=settings.ORG, BOARD_ID=settings.BOARD_ID)
    client = BoardClient(student_client)
    payload = dict(payloads["board"]["article_secret"])
    payload.update(board_id=settings.BOARD_ID, is_secret=True, title=f"pytest-tc57-{uuid4().hex[:10]}")
    article_id = None
    try:
        data = assert_success(client.article_edit(settings.ORG, payload))
        article_id = find_first_value(data, ("board_article_id",))
        assert article_id is not None
        article = _article(client, article_id)
        assert article.get("is_secret") is True
        assert article.get("title") == payload["title"]
    finally:
        if article_id:
            assert_success(client.article_delete(settings.ORG, article_id))


# ---------------------------------------------------------------------------
# TC58 | 본인 게시글 수정 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.destructive
def test_api_58(student_client, payloads):
    require_values(ORG=settings.ORG, OWN_ARTICLE_ID=settings.OWN_ARTICLE_ID, BOARD_ID=settings.BOARD_ID)
    client = BoardClient(student_client)
    payload = dict(payloads["board"]["article_update"])
    payload.update(board_article_id=settings.OWN_ARTICLE_ID, board_id=settings.BOARD_ID)
    payload["title"] = f"pytest-tc58-{uuid4().hex[:10]}"
    assert_success(client.article_edit(settings.ORG, payload))
    article = _article(client, settings.OWN_ARTICLE_ID)
    assert article.get("title") == payload["title"]
    assert article.get("content") == payload["content"]
    assert article.get("is_secret") == payload["is_secret"]


# ---------------------------------------------------------------------------
# TC59 | 본인 게시글 삭제 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.destructive
def test_api_59(student_client):
    require_values(ORG=settings.ORG, OWN_ARTICLE_ID=settings.OWN_ARTICLE_ID)
    client = BoardClient(student_client)
    assert_success(client.article_delete(settings.ORG, settings.OWN_ARTICLE_ID))
    assert_not_success(client.article_get(settings.ORG, settings.OWN_ARTICLE_ID))


# ---------------------------------------------------------------------------
# TC60 | 타인 게시글 수정 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.negative
@pytest.mark.destructive
def test_api_60(student_a_client, student_b_client, payloads):
    require_values(ORG=settings.ORG, OTHER_ARTICLE_ID=settings.OTHER_ARTICLE_ID, BOARD_ID=settings.BOARD_ID)
    attacker = BoardClient(student_a_client)
    owner = BoardClient(student_b_client)
    before = _article(owner, settings.OTHER_ARTICLE_ID)
    original = {k: before.get(k) for k in ("title", "content", "is_secret")}
    payload = dict(payloads["board"]["other_article_update"])
    payload.update(board_article_id=settings.OTHER_ARTICLE_ID, board_id=settings.BOARD_ID)
    response = attacker.article_edit(settings.ORG, payload)
    assert_business_rejected(response, context="TC60 수강생 A의 수강생 B 게시글 수정 차단")
    attacker_after = _article(attacker, settings.OTHER_ARTICLE_ID)
    assert {k: attacker_after.get(k) for k in original} == original
    owner_after = _article(owner, settings.OTHER_ARTICLE_ID)
    assert {k: owner_after.get(k) for k in original} == original


# ---------------------------------------------------------------------------
# TC61 | 타인 게시글 삭제 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.negative
@pytest.mark.destructive
def test_api_61(student_a_client, student_b_client):
    require_values(ORG=settings.ORG, OTHER_ARTICLE_ID=settings.OTHER_ARTICLE_ID)
    attacker = BoardClient(student_a_client); owner = BoardClient(student_b_client)
    assert_permission_denied(attacker.article_delete(settings.ORG, settings.OTHER_ARTICLE_ID))
    article = _article(owner, settings.OTHER_ARTICLE_ID)
    assert str(article.get("id")) == str(settings.OTHER_ARTICLE_ID)


# ---------------------------------------------------------------------------
# TC62 | 학생 게시글 삭제 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.destructive
def test_api_62(educator_client):
    require_values(ORG=settings.ORG, EDUCATOR_DELETE_ARTICLE_ID=settings.EDUCATOR_DELETE_ARTICLE_ID)
    client = BoardClient(educator_client)
    assert_success(client.article_delete(settings.ORG, settings.EDUCATOR_DELETE_ARTICLE_ID))
    assert_not_success(client.article_get(settings.ORG, settings.EDUCATOR_DELETE_ARTICLE_ID))


# ---------------------------------------------------------------------------
# TC63 | 공지사항 작성 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.destructive
def test_api_63(educator_client, payloads):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID)
    _require_real_notice_board(educator_client)
    client = BoardClient(educator_client)
    payload = dict(payloads["board"]["notice_create"])
    payload.update(board_id=settings.NOTICE_BOARD_ID, title=f"pytest-tc63-notice-{uuid4().hex[:10]}")
    article_id = None
    try:
        data = assert_success(client.article_edit(settings.ORG, payload))
        article_id = find_first_value(data, ("board_article_id",))
        assert article_id is not None
        listing = assert_success(client.article_list(settings.ORG, settings.NOTICE_BOARD_ID))
        assert str(article_id) in _article_ids(listing)
    finally:
        if article_id:
            assert_success(client.article_delete(settings.ORG, article_id))


# ---------------------------------------------------------------------------
# TC64 | 공지사항 작성 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.negative
@pytest.mark.destructive
def test_api_64(student_client, educator_client, payloads):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID)
    _require_real_notice_board(educator_client)
    student = BoardClient(student_client)
    payload = dict(payloads["board"]["notice_create"])
    payload.update(board_id=settings.NOTICE_BOARD_ID, title=f"pytest-tc64-blocked-{uuid4().hex[:10]}")
    response = student.article_edit(settings.ORG, payload)
    assert_business_rejected(response, context="TC64 수강생 공지 작성 차단")
    listing = assert_success(BoardClient(educator_client).article_list(settings.ORG, settings.NOTICE_BOARD_ID))
    assert not contains_value(listing, payload["title"])


# ---------------------------------------------------------------------------
# TC65 | 게시판 설정 편집 (교육자)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.destructive
def test_api_65(educator_client):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID, BOARD_ID=settings.BOARD_ID)
    client = BoardClient(educator_client)
    before = _find_board(client, settings.BOARD_ID)
    original = before.get("name")
    changed = f"pytest-tc65-{uuid4().hex[:10]}"
    try:
        assert_success(client.board_edit(settings.ORG, _board_payload(before, changed)))
        after = _find_board(client, settings.BOARD_ID)
        assert after.get("name") == changed
    finally:
        current = _find_board(client, settings.BOARD_ID)
        assert_success(client.board_edit(settings.ORG, _board_payload(current, original)))
        assert _find_board(client, settings.BOARD_ID).get("name") == original


# ---------------------------------------------------------------------------
# TC66 | 게시판 설정 편집 차단 (수강생)
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.negative
@pytest.mark.destructive
def test_api_66(student_client, educator_client):
    require_values(ORG=settings.ORG, COURSE_ID=settings.COURSE_ID, BOARD_ID=settings.BOARD_ID)
    owner = BoardClient(educator_client); attacker = BoardClient(student_client)
    before = _find_board(owner, settings.BOARD_ID)
    original = {k: before.get(k) for k in ("name", "viewable_course_role", "postable_course_role", "commentable_course_role")}
    payload = _board_payload(before, f"pytest-tc66-blocked-{uuid4().hex[:10]}")
    assert_permission_denied(attacker.board_edit(settings.ORG, payload))
    after = _find_board(owner, settings.BOARD_ID)
    assert {k: after.get(k) for k in original} == original


# ---------------------------------------------------------------------------
# TC67 | 타 수강생 비밀글 상세 접근 차단
# ---------------------------------------------------------------------------
@pytest.mark.board
@pytest.mark.negative
@pytest.mark.destructive
def test_api_67(student_a_client, student_b_client, payloads):
    require_values(ORG=settings.ORG, BOARD_ID=settings.BOARD_ID)
    attacker = BoardClient(student_a_client); owner = BoardClient(student_b_client)
    payload = dict(payloads["board"]["article_secret"])
    payload.update(
        board_id=settings.BOARD_ID,
        is_secret=True,
        title=f"pytest-tc67-secret-{uuid4().hex[:10]}",
        content=f"protected-{uuid4().hex}",
    )
    article_id = None
    try:
        create = assert_success(owner.article_edit(settings.ORG, payload))
        article_id = find_first_value(create, ("board_article_id",))
        assert article_id is not None
        response = attacker.article_get(settings.ORG, article_id)
        if response.status_code == 200:
            try:
                assert_permission_denied(response)
            except AssertionError:
                data = response.json()
                assert not contains_value(data, payload["title"])
                assert not contains_value(data, payload["content"])
        else:
            assert_permission_denied(response)
    finally:
        if article_id:
            assert_success(owner.article_delete(settings.ORG, article_id))


# ---------------------------------------------------------------------------
# TC68 | 본문 공백 게시글 작성
# ---------------------------------------------------------------------------
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
