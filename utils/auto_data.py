from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from clients.board_client import BoardClient
from clients.classroom_client import ClassroomClient
from clients.course_client import CourseClient
from clients.schedule_client import ScheduleClient
from config.settings import settings


def _json(response):
    try:
        return response.json()
    except Exception:
        return None


def _is_success(response):
    if response is None or response.status_code != 200:
        return False

    data = _json(response)

    if isinstance(data, dict) and isinstance(data.get("_result"), dict):
        return data["_result"].get("status_code") == 200

    return True


def _walk(data):
    if isinstance(data, dict):
        yield data
        for value in data.values():
            yield from _walk(value)
    elif isinstance(data, list):
        for item in data:
            yield from _walk(item)


def _find_first(data, keys):
    keys = set(keys)
    for node in _walk(data):
        if isinstance(node, dict):
            for key in keys:
                if node.get(key) not in (None, ""):
                    return node[key]
    return None


def _list_at(data, key):
    if isinstance(data, dict) and isinstance(data.get(key), list):
        return data[key]
    return []


class AutoDataResolver:
    """실행 전 테스트에 필요한 ID를 조회하거나 QA 전용 데이터로 생성한다."""

    def __init__(self, educator_api, student_api, student_b_api=None):
        self.educator_api = educator_api
        self.student_api = student_api
        self.student_b_api = student_b_api

        self.educator_classroom = ClassroomClient(educator_api)
        self.student_classroom = ClassroomClient(student_api)
        self.educator_course = CourseClient(educator_api)
        self.student_course = CourseClient(student_api)
        self.educator_schedule = ScheduleClient(educator_api)
        self.student_schedule = ScheduleClient(student_api)
        self.educator_board = BoardClient(educator_api)
        self.student_board = BoardClient(student_api)
        self.student_b_board = (
            BoardClient(student_b_api) if student_b_api else None
        )

        self.created_lectures = []
        self.created_pages = []
        self.created_schedules = []
        self.created_articles = []

        self.messages = []

    def log(self, message):
        self.messages.append(message)
        print(f"[AUTO DATA] {message}")

    def set_if_empty(self, name, value, source):
        if value in (None, ""):
            return False

        if getattr(settings, name, ""):
            return False

        setattr(settings, name, str(value))
        self.log(f"{name}={value}  ← {source}")
        return True

    @staticmethod
    def _fail_code(data):
        if not isinstance(data, dict):
            return None

        if data.get("fail_code"):
            return data.get("fail_code")

        detail = data.get("detail")
        if isinstance(detail, dict):
            if detail.get("fail_code"):
                return detail.get("fail_code")
            resp_json = detail.get("resp_json")
            if isinstance(resp_json, dict):
                return resp_json.get("fail_code")

        return None

    def resolve_org(self):
        """classroom API를 실제 호출해 기관 name_short를 자동 판별한다."""
        if not settings.AUTO_RESOLVE_ORG:
            self.log(f"기관 자동 판별 비활성화: ORG={settings.ORG}")
            return bool(settings.ORG)

        if not settings.CLASSROOM_API_BASE_URL or not settings.CLASSROOM_ID:
            self.log("기관 자동 판별 생략: CLASSROOM API URL/CLASSROOM_ID 없음")
            return bool(settings.ORG)

        candidates = []
        for candidate in [settings.ORG, *settings.ORG_CANDIDATES]:
            candidate = str(candidate or "").strip()
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        url = (
            f"{settings.CLASSROOM_API_BASE_URL.rstrip('/')}"
            f"/classroom/{settings.CLASSROOM_ID}"
        )

        for candidate in candidates:
            for role, api in (
                ("교육자", self.educator_api),
                ("수강생", self.student_api),
            ):
                try:
                    response = api.get(
                        url,
                        headers={"x-elice-org-name-short": candidate},
                    )
                    data = _json(response)
                    fail_code = self._fail_code(data)
                    self.log(
                        f"ORG 후보 {candidate} ({role}) -> "
                        f"HTTP {response.status_code}"
                        + (f", fail_code={fail_code}" if fail_code else "")
                    )

                    if response.status_code == 200:
                        previous = settings.ORG
                        settings.ORG = candidate
                        if previous != candidate:
                            self.log(
                                f"ORG 자동 교정: {previous or '(빈값)'} -> {candidate}"
                            )
                        else:
                            self.log(f"ORG 확인 완료: {candidate}")
                        return True
                except Exception as exc:
                    self.log(
                        f"ORG 후보 {candidate} ({role}) 확인 실패: "
                        f"{type(exc).__name__}: {exc}"
                    )

        self.log(
            "유효한 ORG를 자동 판별하지 못했습니다. "
            f"시도 후보={candidates}. Network의 x-elice-org-name-short 값을 확인하세요."
        )
        return False

    def preflight(self):
        """대량 실행 전에 3개 API 계층의 기본 연결 상태를 로그로 보여준다."""
        self.log(f"PREFLIGHT ORG={settings.ORG}")

        checks = []
        if settings.CLASSROOM_ID:
            checks.append((
                "classroom",
                lambda: self.educator_classroom.get_classroom(settings.CLASSROOM_ID),
            ))
            checks.append((
                "dashboard",
                lambda: self.educator_classroom.get_dashboard_courses(
                    settings.CLASSROOM_ID, offset=0, count=1
                ),
            ))
        if settings.ORG and settings.COURSE_ID:
            checks.append((
                "legacy-course",
                lambda: self.educator_course.course_get(
                    settings.ORG, settings.COURSE_ID
                ),
            ))

        for name, call in checks:
            try:
                response = call()
                data = _json(response)
                fail_code = self._fail_code(data)
                suffix = f", fail_code={fail_code}" if fail_code else ""
                self.log(f"PREFLIGHT {name}: HTTP {response.status_code}{suffix}")
                if response.status_code == 404 and name == "legacy-course":
                    attempted = (
                        f"{settings.API_BASE_URL.rstrip('/')}"
                        f"/org/{settings.ORG}/course/get/?course_id={settings.COURSE_ID}"
                    )
                    self.log(
                        "PREFLIGHT legacy-course가 404입니다. "
                        f"시도 URL={attempted}"
                    )
            except Exception as exc:
                self.log(
                    f"PREFLIGHT {name} 예외: {type(exc).__name__}: {exc}"
                )

    def discover_all(self):
        self.log("자동 테스트 데이터 조회/준비 시작")

        try:
            self.resolve_org()
        except Exception as exc:
            self.log(f"ORG 자동 판별 실패: {type(exc).__name__}: {exc}")

        self.preflight()

        steps = [
            ("학생", self.discover_students),
            ("수업", self.discover_and_prepare_lectures),
            ("수업 자료", self.prepare_materials),
            ("게시판", self.discover_boards),
            ("게시글", self.prepare_articles),
            ("일정", self.prepare_schedules),
        ]

        for label, func in steps:
            try:
                func()
            except Exception as exc:
                self.log(f"{label} 자동 준비 일부 실패: {type(exc).__name__}: {exc}")

        self.log("자동 테스트 데이터 조회/준비 완료")
        return self.summary()

    # ------------------------------------------------------------
    # Student IDs
    # ------------------------------------------------------------
    def discover_students(self):
        if not settings.DASHBOARD_API_BASE_URL or not settings.CLASSROOM_ID:
            return

        response = self.educator_classroom.get_students(
            settings.CLASSROOM_ID,
            offset=0,
            count=10,
        )
        if not _is_success(response):
            self.log(
                f"학생 목록 조회 실패: HTTP {response.status_code} "
                f"BODY={response.text[:800]}"
            )
            return

        data = _json(response)
        records = []

        for node in _walk(data):
            if isinstance(node, dict) and isinstance(node.get("account"), dict):
                records.append(node)

        candidates = []
        for record in records:
            values = []
            if record.get("id") not in (None, ""):
                values.append(record["id"])
            account = record.get("account") or {}
            if account.get("id") not in (None, ""):
                values.append(account["id"])

            for value in values:
                if str(value) not in [str(v) for v in candidates]:
                    candidates.append(value)

        # 학생 본인 토큰으로 실제 접근 가능한 student_id를 찾는다.
        if not settings.STUDENT_ID:
            for candidate in candidates:
                probe = self.student_classroom.get_student_courses(
                    candidate,
                    settings.CLASSROOM_ID,
                    offset=0,
                    count=1,
                )
                if _is_success(probe):
                    self.set_if_empty(
                        "STUDENT_ID",
                        candidate,
                        "교육자 학생목록 + 학생토큰 본인 과목 조회 검증",
                    )
                    break

        if not settings.OTHER_STUDENT_ID:
            for candidate in candidates:
                if str(candidate) != str(settings.STUDENT_ID):
                    self.set_if_empty(
                        "OTHER_STUDENT_ID",
                        candidate,
                        "교육자 학생목록의 다른 학생",
                    )
                    break

    # ------------------------------------------------------------
    # Lectures
    # ------------------------------------------------------------
    def _create_lecture(self, title, parent_lecture_id=None):
        payload = {
            "course_id": settings.COURSE_ID,
            "lecture_type": 0,
            "title": title,
            "description": "",
            "is_opened": True,
            "is_preview": False,
        }
        if parent_lecture_id not in (None, ""):
            payload["parent_lecture_id"] = parent_lecture_id
        response = self.educator_course.lecture_edit(settings.ORG, payload)
        if not _is_success(response):
            self.log(
                "수업 자동 생성 실패: "
                f"HTTP {response.status_code} BODY={response.text[:1200]}"
            )
            return None

        lecture_id = _find_first(_json(response), ("lecture_id",))
        if lecture_id:
            self.created_lectures.append(str(lecture_id))
        return lecture_id

    def _get_lecture_records(self):
        response = self.educator_course.lecture_list(
            settings.ORG,
            settings.COURSE_ID,
        )
        if not _is_success(response):
            self.log(
                "수업 목록 조회 실패: "
                f"HTTP {response.status_code} BODY={response.text[:1200]}"
            )
            return []
        return _list_at(_json(response), "lectures")

    def _find_lecture_record(self, lecture_id):
        for lecture in self._get_lecture_records():
            if str(lecture.get("id")) == str(lecture_id):
                return lecture
        return None

    def _student_can_list_lecture_pages(self, lecture_id):
        response = self.student_course.lecture_page_list(
            settings.ORG,
            lecture_id,
            settings.LOCATOR_TYPE,
            offset=0,
            count=1,
        )
        return _is_success(response)

    def _set_accessible_leaf_lecture(self, lectures):
        # TC22/TC35는 학생 토큰으로 lecture_page/list가 가능해야 하므로
        # depth=1 여부뿐 아니라 실제 학생 접근까지 probe한다.
        leaf_normal = [
            lecture for lecture in lectures
            if lecture.get("depth") == 1
            and lecture.get("lecture_type") == 0
        ]
        leaf_any = [
            lecture for lecture in lectures
            if lecture.get("depth") == 1
            and lecture not in leaf_normal
        ]

        # 열린 것으로 표시된 lecture를 우선 검사한다.
        candidates = sorted(
            leaf_normal + leaf_any,
            key=lambda lecture: (
                lecture.get("is_opened") is not True,
                lecture.get("is_page_readable") is not True,
            ),
        )

        for lecture in candidates:
            lecture_id = lecture.get("id")
            if lecture_id and self._student_can_list_lecture_pages(lecture_id):
                self.set_if_empty(
                    "LECTURE_ID",
                    lecture_id,
                    "학생 접근 가능 depth=1 leaf lecture",
                )
                return True

        return False

    def discover_and_prepare_lectures(self):
        if not settings.API_BASE_URL or not settings.ORG or not settings.COURSE_ID:
            return

        lectures = self._get_lecture_records()

        if not settings.LECTURE_ID:
            self._set_accessible_leaf_lecture(lectures)

        if not settings.AUTO_SETUP_TEST_DATA:
            return

        prefix = f"pytest-auto-{uuid4().hex[:8]}"

        if not settings.EDIT_LECTURE_ID:
            lecture_id = self._create_lecture(f"{prefix}-edit")
            self.set_if_empty(
                "EDIT_LECTURE_ID",
                lecture_id,
                "자동 생성한 수정 전용 수업",
            )

        if not settings.DELETE_LECTURE_ID:
            lecture_id = self._create_lecture(f"{prefix}-delete")
            self.set_if_empty(
                "DELETE_LECTURE_ID",
                lecture_id,
                "자동 생성한 삭제 전용 수업",
            )

        if not settings.BLOCK_DELETE_LECTURE_ID:
            lecture_id = self._create_lecture(f"{prefix}-block-delete")
            self.set_if_empty(
                "BLOCK_DELETE_LECTURE_ID",
                lecture_id,
                "자동 생성한 수강생 삭제차단 검증용 수업",
            )

        if not settings.BLOCK_EDIT_LECTURE_ID:
            lecture_id = self._create_lecture(f"{prefix}-block-edit")
            self.set_if_empty(
                "BLOCK_EDIT_LECTURE_ID",
                lecture_id,
                "자동 생성한 수강생 수정차단 검증용 수업",
            )

        # 기존 leaf들이 모두 학생에게 닫혀 있으면 QA 전용 열린 leaf를 만든다.
        if not settings.LECTURE_ID:
            parent_id = self._create_lecture(f"{prefix}-material-parent")

            if parent_id:
                # top-level 자체가 depth=1인 구조인지 먼저 확인
                parent_record = self._find_lecture_record(parent_id)
                if (
                    parent_record
                    and parent_record.get("depth") == 1
                    and self._student_can_list_lecture_pages(parent_id)
                ):
                    self.set_if_empty(
                        "LECTURE_ID",
                        parent_id,
                        "자동 생성한 학생 접근 가능 depth=1 수업",
                    )
                else:
                    child_id = self._create_lecture(
                        f"{prefix}-material-leaf",
                        parent_lecture_id=parent_id,
                    )
                    if child_id:
                        child_record = self._find_lecture_record(child_id)
                        if (
                            child_record
                            and child_record.get("depth") == 1
                            and self._student_can_list_lecture_pages(child_id)
                        ):
                            self.set_if_empty(
                                "LECTURE_ID",
                                child_id,
                                "자동 생성한 학생 접근 가능 depth=1 leaf 수업",
                            )

        if not settings.LECTURE_ID:
            self.log(
                "학생이 lecture_page/list 할 수 있는 depth=1 수업을 "
                "자동 확보하지 못했습니다."
            )

    # ------------------------------------------------------------
    # Materials
    # ------------------------------------------------------------
    def _material_payload(self, title, content):
        return {
            "lecture_id": settings.LECTURE_ID,
            "title": title,
            "description": "",
            "is_opened": True,
            "is_for_stats": False,
            "locator_types": int(settings.LOCATOR_TYPE or 0),
            "content": content,
        }

    def _find_page_for_note(self, material_note_id, title):
        response = self.educator_course.lecture_page_list(
            settings.ORG,
            settings.LECTURE_ID,
            settings.LOCATOR_TYPE,
        )
        if not _is_success(response):
            return None

        pages = _list_at(_json(response), "lecture_pages")

        for page in pages:
            if str(page.get("material_id")) == str(material_note_id):
                return page.get("id")

        for page in pages:
            if page.get("title") == title:
                return page.get("id")

        return None

    def _create_note(self, title):
        payload = self._material_payload(
            title,
            "pytest requests 자동 준비 테스트 자료",
        )
        response = self.educator_course.material_note_edit(
            settings.ORG,
            payload,
        )
        if not _is_success(response):
            self.log(
                "수업 자료 자동 생성 실패: "
                f"HTTP {response.status_code} BODY={response.text[:1200]}"
            )
            return None, None

        material_note_id = _find_first(
            _json(response),
            ("material_note_id",),
        )
        page_id = self._find_page_for_note(material_note_id, title)

        if page_id:
            self.created_pages.append(str(page_id))

        return material_note_id, page_id

    def prepare_materials(self):
        if not settings.AUTO_SETUP_TEST_DATA or not settings.LECTURE_ID:
            return

        prefix = f"pytest-auto-note-{uuid4().hex[:8]}"

        if not settings.MATERIAL_NOTE_ID:
            material_id, _ = self._create_note(f"{prefix}-edit")
            self.set_if_empty(
                "MATERIAL_NOTE_ID",
                material_id,
                "자동 생성한 수정 전용 수업 자료",
            )

        if not settings.DELETE_LECTURE_PAGE_ID:
            _, page_id = self._create_note(f"{prefix}-delete")
            self.set_if_empty(
                "DELETE_LECTURE_PAGE_ID",
                page_id,
                "자동 생성한 삭제 전용 lecture_page",
            )

        if (
            not settings.BLOCK_MATERIAL_NOTE_ID
            or not settings.BLOCK_DELETE_LECTURE_PAGE_ID
        ):
            material_id, page_id = self._create_note(
                f"{prefix}-block-delete"
            )
            self.set_if_empty(
                "BLOCK_MATERIAL_NOTE_ID",
                material_id,
                "자동 생성한 수강생 자료관리 차단 검증용 자료",
            )
            self.set_if_empty(
                "BLOCK_DELETE_LECTURE_PAGE_ID",
                page_id,
                "자동 생성한 수강생 자료삭제 차단 검증용 lecture_page",
            )

    # ------------------------------------------------------------
    # Boards
    # ------------------------------------------------------------
    def discover_boards(self):
        if not settings.API_BASE_URL or not settings.COURSE_ID:
            return

        response = self.educator_board.board_list(
            settings.ORG,
            settings.COURSE_ID,
        )
        if not _is_success(response):
            self.log(f"게시판 목록 조회 실패: HTTP {response.status_code}")
            return

        boards = _list_at(_json(response), "boards")
        if not boards:
            return

        if not settings.BOARD_ID:
            writable = [
                b for b in boards
                if b.get("is_viewable", True)
                and b.get("is_postable", True)
                and int(b.get("postable_course_role", 999)) <= 45
            ]
            if writable:
                self.set_if_empty(
                    "BOARD_ID",
                    writable[0].get("id"),
                    "GET /board/list/ 학생 작성 가능 게시판",
                )
            else:
                self.log("학생 작성 가능 board를 찾지 못했습니다. 관련 TC는 사전조건 미충족으로 SKIP됩니다.")

        if not settings.NOTICE_BOARD_ID:
            restricted = [
                b for b in boards
                if b.get("is_viewable", True)
                and int(b.get("viewable_course_role", 999)) <= 45
                and int(b.get("postable_course_role", 0)) > 45
            ]

            if restricted:
                self.set_if_empty(
                    "NOTICE_BOARD_ID",
                    restricted[0].get("id"),
                    "GET /board/list/ 학생 작성 제한 공지 후보 게시판",
                )
            else:
                self.log(
                    "학생 작성 제한 공지 board를 찾지 못했습니다. "
                    "TC63/TC64는 사전조건 미충족으로 SKIP되며 게시판 권한을 임의 변경하지 않습니다."
                )

    # ------------------------------------------------------------
    # Articles
    # ------------------------------------------------------------
    def _create_article(self, board_client, title, secret=False):
        payload = {
            "board_id": settings.BOARD_ID,
            "title": title,
            "content": "pytest requests 자동 준비 게시글",
            "is_secret": secret,
        }
        response = board_client.article_edit(settings.ORG, payload)
        if not _is_success(response):
            return None

        article_id = _find_first(
            _json(response),
            ("board_article_id",),
        )
        if article_id:
            self.created_articles.append(
                (board_client, str(article_id))
            )
        return article_id

    def prepare_articles(self):
        if (
            not settings.AUTO_SETUP_TEST_DATA
            or not settings.BOARD_ID
        ):
            # 기존 글에서 상세조회용 ID라도 확보
            if not settings.BOARD_ARTICLE_ID and settings.CLASSROOM_ID:
                response = self.educator_board.classroom_articles(
                    settings.CLASSROOM_ID,
                    count=10,
                )
                data = _json(response)
                if _is_success(response) and isinstance(data, list) and data:
                    self.set_if_empty(
                        "BOARD_ARTICLE_ID",
                        data[0].get("id"),
                        "클래스 게시글 목록",
                    )
            return

        prefix = f"pytest-auto-article-{uuid4().hex[:8]}"

        if not settings.OWN_ARTICLE_ID:
            article_id = self._create_article(
                self.student_board,
                f"{prefix}-own",
            )
            self.set_if_empty(
                "OWN_ARTICLE_ID",
                article_id,
                "학생 토큰으로 자동 생성한 본인 게시글",
            )

        self.set_if_empty(
            "BOARD_ARTICLE_ID",
            settings.OWN_ARTICLE_ID,
            "자동 생성한 본인 게시글 재사용",
        )

        if not settings.EDUCATOR_DELETE_ARTICLE_ID:
            article_id = self._create_article(
                self.student_board,
                f"{prefix}-educator-delete",
            )
            self.set_if_empty(
                "EDUCATOR_DELETE_ARTICLE_ID",
                article_id,
                "학생이 자동 생성한 교육자 삭제 검증용 게시글",
            )

        if self.student_b_board:
            if not settings.OTHER_ARTICLE_ID:
                article_id = self._create_article(
                    self.student_b_board,
                    f"{prefix}-student-b",
                )
                self.set_if_empty(
                    "OTHER_ARTICLE_ID",
                    article_id,
                    "수강생 B가 자동 생성한 타인 게시글",
                )

            if not settings.SECRET_ARTICLE_ID:
                article_id = self._create_article(
                    self.student_b_board,
                    f"{prefix}-student-b-secret",
                    secret=True,
                )
                self.set_if_empty(
                    "SECRET_ARTICLE_ID",
                    article_id,
                    "수강생 B가 자동 생성한 비밀글",
                )

    # ------------------------------------------------------------
    # Schedules
    # ------------------------------------------------------------
    def _schedule_window(self):
        # Windows/Python 환경에서 zoneinfo tzdata가 없어도 동작하도록
        # 한국 표준시 UTC+09:00 고정 오프셋을 사용한다.
        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)

        # 이미 지난 오늘 시간이 아니라 내일부터 테스트 일정을 만든다.
        start = (
            now.replace(hour=0, minute=0, second=0, microsecond=0)
            + timedelta(days=1)
        )
        end = start + timedelta(days=7)

        return start, end

    def _find_schedule(self, summary, start, end, retries=6, delay=0.5):
        """생성 직후 eventual consistency까지 고려해서 일정 ID를 재조회한다."""
        last_response = None

        for attempt in range(1, retries + 1):
            response = self.educator_schedule.list_schedules(
                settings.CLASSROOM_ID,
                start.isoformat(),
                end.isoformat(),
                20,
            )
            last_response = response

            if _is_success(response):
                data = _json(response)

                # 서비스 응답이 list 또는 dict wrapper 어느 쪽이어도 찾는다.
                for node in _walk(data):
                    if (
                        isinstance(node, dict)
                        and node.get("summary") == summary
                        and node.get("id") not in (None, "")
                    ):
                        if attempt > 1:
                            self.log(
                                f"일정 생성 후 {attempt}회차 조회에서 ID 확인: "
                                f"{node.get('id')}"
                            )
                        return node.get("id"), node
            else:
                self.log(
                    f"일정 ID 조회 {attempt}/{retries} 실패: "
                    f"HTTP {response.status_code} BODY={response.text[:800]}"
                )

            if attempt < retries:
                time.sleep(delay)

        if last_response is not None:
            self.log(
                "일정 생성은 성공했지만 목록에서 ID를 찾지 못했습니다. "
                f"summary={summary}, 마지막 응답={last_response.text[:1200]}"
            )
        return None, None

    def _create_schedule(self, summary, offset_hours, live=False):
        start_window, end_window = self._schedule_window()
        dt_start = start_window + timedelta(hours=offset_hours)
        dt_end = dt_start + timedelta(hours=1)

        payload = {
            "classroom_id": settings.CLASSROOM_ID,
            "summary": summary,
            "dt_start": dt_start.isoformat(),
            "dt_end": dt_end.isoformat(),
        }

        if live:
            payload["course_id"] = int(settings.COURSE_ID)
            payload["enable_lectureroom"] = True

        response = self.educator_schedule.create_schedule(payload)
        if not _is_success(response):
            self.log(
                "일정 자동 생성 실패: "
                f"HTTP {response.status_code} BODY={response.text[:1200]}"
            )
            return None, None

        response_data = _json(response)
        schedule_id = _find_first(
            response_data,
            ("schedule_id", "id"),
        )
        schedule = response_data if isinstance(response_data, dict) else None

        # POST 응답에 ID가 없으면 목록을 polling해서 찾는다.
        if not schedule_id:
            schedule_id, schedule = self._find_schedule(
                summary,
                start_window - timedelta(days=1),
                end_window,
            )

        if schedule_id:
            self.created_schedules.append(str(schedule_id))
        else:
            self.log(f"자동 생성 일정 ID 확정 실패: {summary}")

        return schedule_id, schedule

    def prepare_schedules(self):
        if (
            not settings.AUTO_SETUP_TEST_DATA
            or not settings.CLASSROOM_ID
        ):
            return

        prefix = f"pytest-auto-schedule-{uuid4().hex[:8]}"

        if not settings.SCHEDULE_ID:
            sid, _ = self._create_schedule(f"{prefix}-edit", 10)
            self.set_if_empty(
                "SCHEDULE_ID",
                sid,
                "자동 생성한 수정 전용 일정",
            )

        if not settings.DELETE_SCHEDULE_ID:
            sid, _ = self._create_schedule(f"{prefix}-delete", 12)
            self.set_if_empty(
                "DELETE_SCHEDULE_ID",
                sid,
                "자동 생성한 삭제 전용 일정",
            )

        if not settings.BLOCK_DELETE_SCHEDULE_ID:
            sid, _ = self._create_schedule(
                f"{prefix}-block-delete",
                14,
            )
            self.set_if_empty(
                "BLOCK_DELETE_SCHEDULE_ID",
                sid,
                "자동 생성한 수강생 삭제차단 검증용 일정",
            )

        if not settings.BLOCK_UPDATE_SCHEDULE_ID:
            sid, _ = self._create_schedule(
                f"{prefix}-block-update",
                15,
            )
            self.set_if_empty(
                "BLOCK_UPDATE_SCHEDULE_ID",
                sid,
                "자동 생성한 수강생 수정차단 검증용 일정",
            )

        if not settings.LECTUREROOM_ID:
            sid, schedule = self._create_schedule(
                f"{prefix}-live",
                16,
                live=True,
            )

            if sid:
                # 상세조회에 live-room 정보가 더 있을 수 있으므로 다시 조회
                detail_response = self.educator_schedule.get_schedule(
                    sid,
                    settings.CLASSROOM_ID,
                )
                detail = _json(detail_response) if _is_success(detail_response) else schedule

                lectureroom_id = _find_first(
                    detail,
                    (
                        "lectureroom_id",
                        "lecture_room_id",
                        "lectureroomId",
                    ),
                )
                self.set_if_empty(
                    "LECTUREROOM_ID",
                    lectureroom_id,
                    "자동 생성한 라이브 일정 응답",
                )

    # ------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------
    def cleanup(self):
        self.log("자동 준비 데이터 정리 시작")

        for client, article_id in reversed(self.created_articles):
            try:
                client.article_delete(settings.ORG, article_id)
            except Exception:
                pass

        for schedule_id in reversed(self.created_schedules):
            try:
                self.educator_schedule.delete_schedule(
                    schedule_id,
                    settings.CLASSROOM_ID,
                )
            except Exception:
                pass

        for page_id in reversed(self.created_pages):
            try:
                self.educator_course.lecture_page_delete_bulk(
                    settings.ORG,
                    page_id,
                )
            except Exception:
                pass

        for lecture_id in reversed(self.created_lectures):
            try:
                self.educator_course.lecture_delete(
                    settings.ORG,
                    lecture_id,
                )
            except Exception:
                pass

        self.log("자동 준비 데이터 정리 완료")

    def summary(self):
        names = [
            "STUDENT_ID",
            "OTHER_STUDENT_ID",
            "COURSE_ID",
            "LECTURE_ID",
            "EDIT_LECTURE_ID",
            "DELETE_LECTURE_ID",
            "BLOCK_DELETE_LECTURE_ID",
            "BLOCK_EDIT_LECTURE_ID",
            "MATERIAL_NOTE_ID",
            "DELETE_LECTURE_PAGE_ID",
            "BLOCK_MATERIAL_NOTE_ID",
            "BLOCK_DELETE_LECTURE_PAGE_ID",
            "SCHEDULE_ID",
            "DELETE_SCHEDULE_ID",
            "BLOCK_DELETE_SCHEDULE_ID",
            "BLOCK_UPDATE_SCHEDULE_ID",
            "LECTUREROOM_ID",
            "BOARD_ID",
            "NOTICE_BOARD_ID",
            "BOARD_ARTICLE_ID",
            "OWN_ARTICLE_ID",
            "OTHER_ARTICLE_ID",
            "EDUCATOR_DELETE_ARTICLE_ID",
            "SECRET_ARTICLE_ID",
        ]
        return {
            name: getattr(settings, name, "")
            for name in names
        }
