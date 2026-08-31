import re

from playwright.sync_api import expect


class ExamResultPage:
    """테스트 결과 페이지"""

    def __init__(self, page):
        self.page = page
        self.test_complete_message = page.get_by_text(
            "테스트 응시 완료",
            exact=True,
        )
        self.view_answers_button = page.get_by_role(
            "button",
            name="답안 보기",
            exact=True,
        )
        self.question_button = page.get_by_role(
            "button",
            name=re.compile(r"^01\s+test"),
        )
        self.answer_input = page.locator("#quiz-text-answer")

    def verify_loaded(self):
        """테스트 결과 페이지 전환 확인"""
        expect(self.test_complete_message).to_be_visible()

    def open_answers(self):
        """제출 답안 보기"""
        self.view_answers_button.click()

    def open_question(self):
        """첫 번째 문제 열기"""
        self.question_button.click()

    def verify_answer(self, answer):
        """제출한 답안 확인"""
        expect(self.answer_input).to_have_value(answer)
