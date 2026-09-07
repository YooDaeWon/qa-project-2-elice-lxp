import re

from playwright.sync_api import expect


class CourseListPage:
    """학습 과목 목록 페이지"""

    URL = re.compile(r"/classrooms/[^/]+/courses/?$")

    def __init__(self, page):
        self.page = page
        self.sandbox_card = page.get_by_role(
            "button",
            name=re.compile(r"^SANDBOX\s+SANDBOX$"),
        )
        self.page_title = page.get_by_text(
            "학습 과목 목록",
            exact=True,
        )
        self.course_page_marker = page.get_by_role(
            "tab",
            name="수업 목록",
            exact=True,
        )

    def verify_loaded(self):
        """학습 과목 목록 페이지 확인"""
        expect(self.page).to_have_url(self.URL)
        expect(self.page_title).to_be_visible()

    def open(self):
        """현재 클래스의 학습 과목 목록 페이지 직접 열기"""
        course_list_url = re.sub(
            r"/courses(?:/.*)?$",
            "/courses",
            self.page.url,
        )
        assert course_list_url != self.page.url, (
            f"학습 과목 목록 URL 생성 실패: {self.page.url}"
        )
        self.page.goto(course_list_url)

    def verify_page_title(self):
        """학습 과목 목록 제목 확인"""
        self.wait_for_list_or_course()

        assert not self.course_page_marker.is_visible(), (
            "학습 과목 버튼이 학습 과목 목록이 아닌 SANDBOX 페이지로 이동함"
        )

    def wait_for_list_or_course(self):
        """목록 제목 또는 과목의 수업 목록 탭 표시까지 대기"""
        page_state = self.page_title.or_(self.course_page_marker).first
        expect(page_state).to_be_visible()

    def is_course_list_visible(self):
        """학습 과목 목록 표시 여부 확인"""
        return self.page_title.is_visible()

    def open_sandbox(self):
        """SANDBOX 과목 페이지 열기"""
        self.sandbox_card.click()
