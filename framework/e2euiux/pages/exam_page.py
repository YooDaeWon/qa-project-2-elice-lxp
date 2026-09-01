from playwright.sync_api import expect


class ExamPage:
    """테스트 응시 페이지"""

    def __init__(self, page):
        self.page = page
        self.answer_input = page.locator("#quiz-text-answer")
        self.submit_button = page.get_by_role(
            "button",
            name="제출",
            exact=True,
        )
        self.end_test_button = page.get_by_role(
            "button",
            name="테스트 종료",
            exact=True,
        )
        self.confirmation_checkbox = page.locator('input[type="checkbox"]')
        self.submit_complete_message = page.get_by_text(
            "제출 완료",
            exact=True,
        )
        self.question_load_error_message = page.get_by_text(
            "테스트 문제를 불러오는 중 문제가 발생하였습니다.",
            exact=True,
        )

    def verify_loaded(self):
        """테스트 응시 페이지 확인"""
        expect(self.submit_button).to_be_visible()

    def enter_answer(self, answer):
        """답안 입력"""
        self.answer_input.click()
        self.answer_input.fill(answer)
        self.page.wait_for_timeout(500)

    def verify_answer_saved(self, answer):
        """새로고침 후 답안 유지 확인"""
        expect(self.answer_input).to_have_value(answer)

    def verify_question_load_error(self):
        """테스트 문제 불러오기 오류 확인"""
        expect(self.question_load_error_message).to_be_visible(
            timeout=10_000,
        )

    def submit_answer(self):
        """답안 제출"""
        self.submit_button.click()

    def verify_submit_enabled(self):
        """제출 버튼 활성화 여부 확인"""
        expect(self.submit_button).to_be_enabled()

    def verify_submit_complete(self):
        """제출 완료 메시지 확인"""
        expect(self.submit_complete_message).to_be_visible()

    def open_end_modal(self):
        """테스트 종료 모달 열기"""
        self.end_test_button.first.click()

    def verify_end_modal_open(self):
        """테스트 종료 모달 확인"""
        expect(self.confirmation_checkbox).to_be_visible()

    def check_end_confirmation(self):
        """테스트 종료 확인 사항 체크"""
        self.confirmation_checkbox.check()

    def verify_end_enabled(self):
        """테스트 종료 버튼 활성화 여부 확인"""
        expect(self.end_test_button.last).to_be_enabled()

    def confirm_end_test(self):
        """테스트 종료"""
        self.end_test_button.last.click()
