"""페이지 객체 모음"""

from .classroom_page import ClassroomPage
from .board_list_page import BoardListPage
from .board_post_page import BoardPostPage
from .board_write_page import BoardWritePage
from .course_list_page import CourseListPage
from .course_page import CoursePage
from .login_page import LoginPage
from .main_page import MainPage
from .my_classes_page import MyClassesPage
from .schedule_page import SchedulePage
from .exam_status_page import ExamStatusPage
from .exam_complete_page import ExamCompletePage
from .exam_notice_page import ExamNoticePage
from .exam_page import ExamPage
from .exam_prepare_page import ExamPreparePage
from .exam_result_page import ExamResultPage
from .exam_time_page import ExamTimePage


__all__ = [
    "BoardListPage",
    "BoardPostPage",
    "BoardWritePage",
    "ClassroomPage",
    "CourseListPage",
    "CoursePage",
    "ExamCompletePage",
    "ExamNoticePage",
    "ExamPage",
    "ExamPreparePage",
    "ExamResultPage",
    "ExamTimePage",
    "LoginPage",
    "ExamStatusPage",
    "MainPage",
    "MyClassesPage",
    "SchedulePage",
]
