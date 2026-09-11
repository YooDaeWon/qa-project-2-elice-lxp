from config.settings import settings


class ClassroomClient:
    def __init__(self, api_client):
        self.api = api_client
        self.classroom_base = settings.CLASSROOM_API_BASE_URL.rstrip("/")
        self.dashboard_base = settings.DASHBOARD_API_BASE_URL.rstrip("/")

    def get_classroom(self, classroom_id):
        return self.api.get(f"{self.classroom_base}/classroom/{classroom_id}")

    def patch_classroom(self, classroom_id, payload):
        return self.api.patch(
            f"{self.classroom_base}/classroom/{classroom_id}",
            json=payload,
        )

    def get_student_courses(
        self,
        student_id,
        classroom_id,
        offset=0,
        count=10,
        sort_by=None,
    ):
        params = {
            "classroom_id": classroom_id,
            "offset": offset,
            "count": count,
        }
        if sort_by:
            params["sort_by"] = sort_by

        return self.api.get(
            f"{self.dashboard_base}/student/{student_id}/course",
            params=params,
        )

    def get_dashboard_courses(self, classroom_id, offset=0, count=3):
        return self.api.get(
            f"{self.dashboard_base}/course",
            params={
                "classroom_id": classroom_id,
                "offset": offset,
                "count": count,
            },
        )

    def get_students(self, classroom_id, offset=0, count=10):
        return self.api.get(
            f"{self.dashboard_base}/student",
            params={
                "classroom_id": classroom_id,
                "offset": offset,
                "count": count,
            },
        )

    @staticmethod
    def _date_only(value):
        if isinstance(value, str) and len(value) >= 10:
            return value[:10]
        return value

    def get_schedule_summary(self, classroom_id, date_start, date_end):
        # schedule/summary의 date_start/date_end는 정확한 날짜(YYYY-MM-DD)만 허용.
        return self.api.get(
            f"{self.classroom_base}/schedule/summary",
            params={
                "classroom_id": classroom_id,
                "date_start": self._date_only(date_start),
                "date_end": self._date_only(date_end),
            },
        )

    def get_schedule_by_date(self, classroom_id, date):
        return self.api.get(
            f"{self.classroom_base}/schedule/by_date",
            params={
                "classroom_id": classroom_id,
                "date": date,
            },
        )

    def get_articles(
        self,
        classroom_id,
        sort_by="created_desc",
        skip=0,
        count=3,
        filter_title=None,
    ):
        params = {
            "sort_by": sort_by,
            "skip": skip,
            "count": count,
        }
        if filter_title:
            params["filter_title"] = filter_title

        return self.api.get(
            f"{self.classroom_base}/classroom/{classroom_id}/article",
            params=params,
        )
