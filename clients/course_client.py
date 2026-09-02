import json

from config.settings import settings


def _multipart(payload):
    def encode(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
    return [(key, (None, encode(value))) for key, value in payload.items()]


COURSE_EDIT_REQUIRED_FIELDS = (
    "is_recommended",
    "is_chat_room_disabled",
    "is_post_student_info_visible",
    "is_post_student_email_enabled",
    "is_post_tutor_email_enabled",
    "is_enroll_noti_enabled",
    "enroll_type",
    "price",
    "completion_info",
    "title",
    "course_type",
    "code",
    "description",
    "short_description",
    "target_audience",
    "objective",
    "faq",
    "class_times",
    "class_type",
    "period",
    "info_summary_visibility_dict",
    "leaderboard_info",
)

COURSE_EDIT_JSON_FIELDS = {
    "completion_info",
    "target_audience",
    "objective",
    "faq",
    "class_times",
    "info_summary_visibility_dict",
    "leaderboard_info",
}


class CourseClient:
    def __init__(self, api_client):
        self.api = api_client
        self.base = settings.API_BASE_URL.rstrip("/")
        self.classroom_base = settings.CLASSROOM_API_BASE_URL.rstrip("/")

    def classroom_course_list(self, classroom_id, skip=0, count=10):
        return self.api.get(
            f"{self.classroom_base}/classroom/{classroom_id}/course",
            params={"skip": skip, "count": count},
        )

    def course_get(self, org, course_id):
        return self.api.get(
            f"{self.base}/org/{org}/course/get/",
            params={"course_id": course_id},
        )

    def lecture_list(self, org, course_id, offset=0, count=40):
        return self.api.get(
            f"{self.base}/org/{org}/lecture/list/",
            params={
                "course_id": course_id,
                "offset": offset,
                "count": count,
            },
        )

    def lecture_page_list(
        self,
        org,
        lecture_id,
        locator_type,
        offset=0,
        count=100,
    ):
        return self.api.get(
            f"{self.base}/org/{org}/lecture_page/list/",
            params={
                "lecture_id": lecture_id,
                "locator_type": locator_type,
                "offset": offset,
                "count": count,
            },
        )

    @staticmethod
    def _encode_course_edit_value(key, value):
        if key in COURSE_EDIT_JSON_FIELDS:
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        if isinstance(value, bool):
            # legacy API cassette와 동일한 form boolean 직렬화
            return "True" if value else "False"
        return value

    def build_course_edit_params(self, course: dict, overrides=None) -> dict:
        """course/get 결과로 course/edit의 필수 Query Params를 자동 구성한다."""
        if not isinstance(course, dict):
            raise ValueError("course/get 응답의 course 객체가 없습니다.")

        raw = {}
        for key in COURSE_EDIT_REQUIRED_FIELDS:
            if key in course and course[key] is not None:
                raw[key] = course[key]

        raw["course_id"] = course.get("id") or course.get("course_id")

        if overrides:
            raw.update(overrides)

        missing = [
            key for key in COURSE_EDIT_REQUIRED_FIELDS
            if key not in raw or raw[key] is None
        ]
        if raw.get("course_id") in (None, ""):
            missing.append("course_id")

        if missing:
            raise ValueError(
                "course/edit 필수값을 course/get 응답에서 만들지 못했습니다: "
                + ", ".join(missing)
            )

        return {
            key: self._encode_course_edit_value(key, value)
            for key, value in raw.items()
        }

    def course_edit(self, org, payload):
        # API 명세 표의 In 열은 query로 표시되어 있으나,
        # 실제 backend cassette와 실제 응답은 POST form fields를 사용한다.
        return self.api.post(
            f"{self.base}/org/{org}/course/edit/",
            data=payload,
        )

    def lecture_edit(self, org, payload):
        return self.api.post(
            f"{self.base}/org/{org}/lecture/edit/",
            data=payload,
        )

    def lecture_delete(self, org, lecture_id):
        return self.api.post(
            f"{self.base}/org/{org}/lecture/delete/",
            files=_multipart({"lecture_id": lecture_id}),
        )

    def material_note_edit(self, org, payload):
        return self.api.post(
            f"{self.base}/org/{org}/material_note/edit/",
            files=_multipart(payload),
        )

    def lecture_page_delete_bulk(self, org, lecture_page_id):
        return self.api.post(
            f"{self.base}/org/{org}/lecture_page/delete/bulk/",
            files=_multipart({"lecture_page_ids": lecture_page_id}),
        )
