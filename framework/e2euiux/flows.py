"""여러 TC에서 반복되는 로그인·페이지 이동 절차"""

from framework.e2euiux.pages import (
    ClassroomPage,
    CourseListPage,
    CoursePage,
    ExamNoticePage,
    ExamPreparePage,
    ExamTimePage,
    LoginPage,
    MainPage,
    MyClassesPage,
)


def login_to_main(page, credentials):
    """LXP 메인 페이지 로그인"""
    login_page = LoginPage(page)
    login_page.open()
    login_page.login(credentials["user_id"], credentials["password"])
    login_page.verify_redirect()


def open_classroom_from_main(page):
    """메인에서 내 클래스를 거쳐 프로젝트 클래스 열기"""
    main_page = MainPage(page)
    main_page.open_my_classes()

    my_classes_page = MyClassesPage(page)
    my_classes_page.verify_loaded()
    my_classes_page.open_classroom()
    return ClassroomPage(page)


def open_sandbox_for_setup(page):
    """학습 과목 클릭 후 도착한 화면에서 시험 사전조건 준비"""
    course_list_page = CourseListPage(page)
    course_page = CoursePage(page)
    course_list_page.wait_for_list_or_course()

    if course_list_page.is_course_list_visible():
        course_list_page.open_sandbox()

    course_page.verify_loaded()
    return course_page


def open_sandbox_from_course_list(page):
    """목록 복구 후 SANDBOX 카드 클릭 경로 검증"""
    course_list_page = CourseListPage(page)
    course_page = CoursePage(page)
    course_list_page.wait_for_list_or_course()

    if not course_list_page.is_course_list_visible():
        course_page.open_course_list()

    course_list_page.verify_loaded()
    course_list_page.open_sandbox()
    course_page.verify_loaded()


def open_exam_notice(page):
    """시험 사전조건 페이지 열기"""
    prepare_page = ExamPreparePage(page)
    prepare_page.verify_loaded()
    prepare_page.agree_and_next()

    time_page = ExamTimePage(page)
    time_page.verify_loaded()
    time_page.go_next()

    notice_page = ExamNoticePage(page)
    notice_page.verify_loaded()
    return notice_page
