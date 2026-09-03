import re

from playwright.sync_api import expect


class SchedulePage:
    """수업 일정 페이지"""

    URL = re.compile(r"/classrooms/[^/]+/schedules/?$")

    def __init__(self, page):
        self.page = page
        self.today_button = page.get_by_role(
            "button",
            name="오늘",
            exact=True,
        )
        self.create_button = page.get_by_role(
            "button",
            name="만들기",
            exact=True,
        )
        self.test_schedule = page.get_by_text(
            "test",
            exact=True,
        )
        self.schedule_title_input = page.locator(
            'input[name="summary"]',
        )
        self.create_dialog = page.get_by_role(
            "dialog",
            name="수업 일정 만들기",
            exact=True,
        )
        self.saved_toast = page.get_by_text(
            "저장되었습니다.",
            exact=True,
        )
        self.delete_button = page.locator(
            'button:has([data-testid="trashIcon"])',
        )
        self.delete_dialog = page.get_by_role(
            "dialog",
            name="일정 삭제",
            exact=True,
        )
        self.delete_confirm_button = self.delete_dialog.get_by_role(
            "button",
            name="삭제",
            exact=True,
        )
        self.linked_class_button = page.locator(
            '[role="button"]:has([data-testid="arrow-rightIcon"])',
        )

    def verify_loaded(self):
        """수업 일정 페이지 확인"""
        expect(self.page).to_have_url(self.URL)
        expect(self.today_button).to_be_visible()

    def open_create(self):
        """수업 일정 만들기 열기"""
        self.create_button.click()

    def verify_create_modal(self):
        """수업 일정 만들기 모달 확인"""
        expect(self.create_dialog).to_be_visible()

    def save_schedule(self):
        """수업 일정 저장"""
        self.create_dialog.get_by_role(
            "button",
            name="저장",
            exact=True,
        ).click()

    def fill_schedule_title(self, title):
        """수업 일정 제목 입력"""
        self.schedule_title_input.fill(title)

    def verify_saved_toast(self):
        """일정 저장 토스트 확인"""
        expect(self.saved_toast).to_be_visible()

    def get_schedule_event(self, title):
        """제목으로 수업 일정 찾기"""
        return self.page.locator(".fc-event").filter(
            has_text=title,
        )

    def verify_schedule_saved(self, title):
        """저장된 수업 일정 확인"""
        expect(self.get_schedule_event(title).last).to_be_visible()

    def open_schedule(self, title):
        """제목으로 수업 일정 열기"""
        self.get_schedule_event(title).last.click()

    def verify_schedule_panel(self):
        """일정 상세 사이드 패널 확인"""
        expect(self.delete_button).to_be_visible()

    def click_trash_icon(self):
        """일정 삭제 아이콘 클릭"""
        self.delete_button.click()
        expect(self.delete_dialog).to_be_visible()

    def verify_delete_modal(self):
        """일정 삭제 모달 확인"""
        expect(self.delete_dialog).to_be_visible()

    def delete_schedule(self):
        """일정 삭제"""
        self.page.wait_for_timeout(500)
        self.delete_confirm_button.click()

    def verify_deleted_toast(self):
        """일정 삭제 토스트 확인"""
        expect(
            self.page.get_by_text(
                "삭제되었습니다.",
                exact=True,
            )
        ).to_be_visible()

    def verify_schedule_deleted(self, title):
        """수업 일정 삭제 결과 확인"""
        expect(self.get_schedule_event(title)).to_have_count(0)

    def open_test_schedule(self):
        """test 일정 열기"""
        self.test_schedule.click()

    def verify_test_panel(self):
        """test 수업 사이드 패널 확인"""
        expect(self.linked_class_button).to_be_visible()

    def click_linked_class_button(self):
        """Click linked class button"""
        self.linked_class_button.click()
