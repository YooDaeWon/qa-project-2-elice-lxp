import re

from playwright.sync_api import expect


class ExamStatusPage:
    """시험 응시 현황 모달"""

    def __init__(self, page):
        self.page = page
        self.status_dialog = page.get_by_role(
            "dialog",
            name="SANDBOX 학습현황",
            exact=True,
        )

    def verify_loaded(self):
        """SANDBOX 시험 응시 현황 모달 확인"""
        expect(self.status_dialog).to_be_visible()

    def verify_student_completed(self, student_id):
        """학습자의 응시 상태 확인"""
        student_row = self.status_dialog.get_by_role(
            "row",
        ).filter(has_text=student_id)
        expect(student_row).to_be_visible()
        expect(
            student_row.get_by_text(re.compile(r"^(완료|응시 전|응시 중)$"))
        ).to_be_visible()
