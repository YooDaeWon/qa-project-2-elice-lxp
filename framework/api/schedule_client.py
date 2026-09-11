from copy import deepcopy
from datetime import datetime, timezone

from config.settings import settings


class ScheduleClient:
    def __init__(self, api_client):
        self.api = api_client
        self.classroom_base = settings.CLASSROOM_API_BASE_URL.rstrip("/")
        self.legacy_base = settings.API_BASE_URL.rstrip("/")

    @staticmethod
    def _parse_datetime(value):
        if not isinstance(value, str):
            return None
        raw = value.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(raw, fmt)
                except ValueError:
                    pass
        return None

    @classmethod
    def _canonical_datetime(cls, value):
        """실제 QA Calendar가 수용한 UTC millisecond Z 형식으로 한 번만 요청한다."""
        dt = cls._parse_datetime(value)
        if dt is None:
            return value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    @classmethod
    def _normalize_payload(cls, payload):
        item = deepcopy(payload)
        for key in ("dt_start", "dt_end", "reschedule_source_dt"):
            if item.get(key):
                item[key] = cls._canonical_datetime(item[key])
        return item

    def list_schedules(self, classroom_id, dt_start_ge, dt_start_le, count=100):
        return self.api.get(
            f"{self.classroom_base}/schedule",
            params={
                "classroom_id": classroom_id,
                "dt_start_ge": self._canonical_datetime(dt_start_ge),
                "dt_start_le": self._canonical_datetime(dt_start_le),
                "count": count,
            },
        )

    def create_schedule(self, payload):
        return self.api.post(
            f"{self.classroom_base}/schedule",
            json=self._normalize_payload(payload),
        )

    def get_schedule(self, schedule_id, classroom_id):
        return self.api.get(
            f"{self.classroom_base}/schedule/{schedule_id}",
            params={"classroom_id": classroom_id},
        )

    def patch_schedule(self, schedule_id, payload):
        return self.api.patch(
            f"{self.classroom_base}/schedule/{schedule_id}",
            json=self._normalize_payload(payload),
        )

    def delete_schedule(self, schedule_id, classroom_id):
        return self.api.delete(
            f"{self.classroom_base}/schedule/{schedule_id}",
            json={"classroom_id": classroom_id},
        )

    def join_lectureroom(self, org, lectureroom_id, role):
        return self.api.post(
            f"{self.legacy_base}/org/{org}/course/lectureroom/join/",
            data={"lectureroom_id": lectureroom_id, "role": role},
        )
