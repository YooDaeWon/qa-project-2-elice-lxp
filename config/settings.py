import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _list_env(name: str, default: str = "") -> list[str]:
    raw = _env(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    API_BASE_URL = _env("API_BASE_URL")
    CLASSROOM_API_BASE_URL = _env("CLASSROOM_API_BASE_URL")
    DASHBOARD_API_BASE_URL = _env("DASHBOARD_API_BASE_URL")
    ACCOUNT_API_BASE_URL = _env("ACCOUNT_API_BASE_URL")

    AUTH_HEADER = _env("AUTH_HEADER", "Authorization")
    # 따옴표로 "Bearer "를 넣어 trailing space 유지
    AUTH_PREFIX = os.getenv("AUTH_PREFIX", "Bearer ")
    AUTH_COOKIE_NAME = _env("AUTH_COOKIE_NAME")

    STSESSION_KEY = _env("STSESSION_KEY")
    TCSESSION_KEY = _env("TCSESSION_KEY")
    STSESSION_A_KEY = _env("STSESSION_A_KEY")
    STSESSION_B_KEY = _env("STSESSION_B_KEY")

    # 개발가이드의 기관 경로는 /org/academy/... 이다.
    # 기존 .env에 qatrack이 남아 있어도 AUTO_DISCOVER 시 후보를 실제 API로 검사해 교정한다.
    ORG = _env("ORG", "academy")
    ORG_CANDIDATES = _list_env("ORG_CANDIDATES", "academy,qatrack")

    CLASSROOM_ID = _env("CLASSROOM_ID")
    STUDENT_ID = _env("STUDENT_ID")
    OTHER_STUDENT_ID = _env("OTHER_STUDENT_ID")

    COURSE_ID = _env("COURSE_ID")
    LECTURE_ID = _env("LECTURE_ID")
    EDIT_LECTURE_ID = _env("EDIT_LECTURE_ID")
    DELETE_LECTURE_ID = _env("DELETE_LECTURE_ID")
    BLOCK_DELETE_LECTURE_ID = _env("BLOCK_DELETE_LECTURE_ID")
    BLOCK_EDIT_LECTURE_ID = _env("BLOCK_EDIT_LECTURE_ID")

    MATERIAL_NOTE_ID = _env("MATERIAL_NOTE_ID")
    DELETE_LECTURE_PAGE_ID = _env("DELETE_LECTURE_PAGE_ID")
    BLOCK_MATERIAL_NOTE_ID = _env("BLOCK_MATERIAL_NOTE_ID")
    BLOCK_DELETE_LECTURE_PAGE_ID = _env("BLOCK_DELETE_LECTURE_PAGE_ID")
    LOCATOR_TYPE = _env("LOCATOR_TYPE", "0")

    SCHEDULE_ID = _env("SCHEDULE_ID")
    DELETE_SCHEDULE_ID = _env("DELETE_SCHEDULE_ID")
    BLOCK_DELETE_SCHEDULE_ID = _env("BLOCK_DELETE_SCHEDULE_ID")
    BLOCK_UPDATE_SCHEDULE_ID = _env("BLOCK_UPDATE_SCHEDULE_ID")
    LECTUREROOM_ID = _env("LECTUREROOM_ID")

    BOARD_ID = _env("BOARD_ID")
    NOTICE_BOARD_ID = _env("NOTICE_BOARD_ID")
    BOARD_ARTICLE_ID = _env("BOARD_ARTICLE_ID")
    OWN_ARTICLE_ID = _env("OWN_ARTICLE_ID")
    OTHER_ARTICLE_ID = _env("OTHER_ARTICLE_ID")
    EDUCATOR_DELETE_ARTICLE_ID = _env("EDUCATOR_DELETE_ARTICLE_ID")
    SECRET_ARTICLE_ID = _env("SECRET_ARTICLE_ID")

    DATE_START = _env("DATE_START")
    DATE_END = _env("DATE_END")
    SCHEDULE_COUNT = int(_env("SCHEDULE_COUNT", "20") or "20")

    AUTO_DISCOVER = _bool_env("AUTO_DISCOVER", True)
    AUTO_RESOLVE_ORG = _bool_env("AUTO_RESOLVE_ORG", True)
    AUTO_SETUP_TEST_DATA = _bool_env("AUTO_SETUP_TEST_DATA", True)
    AUTO_CLEANUP = _bool_env("AUTO_CLEANUP", False)
    EMPTY_CONTENT_POLICY = _env("EMPTY_CONTENT_POLICY", "reject").lower()


settings = Settings()
