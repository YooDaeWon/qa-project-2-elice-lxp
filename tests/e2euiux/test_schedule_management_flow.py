import secrets

import allure
import pytest

from framework.e2euiux.pages import (
    ClassroomPage,
    LoginPage,
    MainPage,
    MyClassesPage,
    SchedulePage,
)


pytestmark = [
    pytest.mark.schedule_management_flow,
    allure.label("owner", "hongseongwoo"),
    allure.label("team", "QA4"),
]


@pytest.fixture(scope="module")
def schedule_title():
    """수업 일정용 8자리 난수 제목"""
    return secrets.token_hex(4)


@allure.label("tc_id", "27")
@allure.label("priority", "P1")
def test_login(e2e_page, educator_credentials):
    """교육자 로그인"""
    login_page = LoginPage(e2e_page)
    login_page.open()
    login_page.login(
        educator_credentials["user_id"],
        educator_credentials["password"],
    )
    login_page.verify_redirect()


@allure.label("tc_id", "28")
@allure.label("priority", "P1")
def test_open_schedule(e2e_page):
    """수업 일정 페이지 진입"""
    main_page = MainPage(e2e_page)
    main_page.open_my_classes()

    my_classes_page = MyClassesPage(e2e_page)
    my_classes_page.verify_loaded()
    my_classes_page.open_classroom()

    classroom_page = ClassroomPage(e2e_page)
    classroom_page.verify_educator_loaded()
    classroom_page.open_schedule()

    schedule_page = SchedulePage(e2e_page)
    schedule_page.verify_loaded()


@allure.label("tc_id", "29")
@allure.label("priority", "P1")
def test_open_create_schedule(e2e_page):
    """수업 일정 만들기 모달 확인"""
    schedule_page = SchedulePage(e2e_page)
    schedule_page.open_create()
    schedule_page.verify_create_modal()


@allure.label("tc_id", "30")
@allure.label("priority", "P1")
def test_save_schedule(e2e_page, schedule_title):
    """수업 일정 저장 토스트 확인"""
    schedule_page = SchedulePage(e2e_page)
    schedule_page.fill_schedule_title(schedule_title)
    schedule_page.save_schedule()
    schedule_page.verify_saved_toast()


@allure.label("tc_id", "31")
@allure.label("priority", "P1")
def test_verify_saved_schedule(e2e_page, schedule_title):
    """오늘 날짜 일정 저장 확인"""
    schedule_page = SchedulePage(e2e_page)
    schedule_page.verify_schedule_saved(schedule_title)


@allure.label("tc_id", "32")
@allure.label("priority", "P1")
def test_open_schedule_detail(e2e_page, schedule_title):
    """저장된 일정 상세 패널 확인"""
    schedule_page = SchedulePage(e2e_page)
    schedule_page.open_schedule(schedule_title)
    schedule_page.verify_schedule_panel()


@allure.label("tc_id", "33")
@allure.label("priority", "P1")
def test_open_delete_modal(e2e_page):
    """일정 삭제 모달 확인"""
    schedule_page = SchedulePage(e2e_page)
    schedule_page.click_trash_icon()
    schedule_page.verify_delete_modal()


@allure.label("tc_id", "34")
@allure.label("priority", "P1")
def test_delete_schedule(e2e_page):
    """일정 삭제 토스트 확인"""
    schedule_page = SchedulePage(e2e_page)
    schedule_page.delete_schedule()
    schedule_page.verify_deleted_toast()


@allure.label("tc_id", "35")
@allure.label("priority", "P1")
def test_verify_schedule_deleted(e2e_page, schedule_title):
    """일정 삭제 결과 확인"""
    schedule_page = SchedulePage(e2e_page)
    schedule_page.verify_schedule_deleted(schedule_title)
