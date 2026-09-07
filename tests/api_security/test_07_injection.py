"""인젝션(웹 취약점) 보안 테스트 (ID 37~42)

대상: LXP(dev-qatrack-api), classroom-api, dashboard-api
검증 방식: TC의 '기대 결과' 기준. 입력값이 데이터가 아닌 명령으로 취급되면 실패(빨간불).

인젝션 계열 보안 이슈:
- XSS: 사용자 입력의 스크립트 태그가 무해화 없이 저장·반사되면 타 사용자 브라우저에서 실행
- SQLi: 입력값이 SQL 구문으로 해석되면 데이터 열람·조작 가능
- CORS: 허용 출처를 화이트리스트로 관리하지 않으면 악성 사이트가 인증정보로 API 호출 가능

ID-38만 실행 방식이 다르다.
판정 기준이 "저장된 스크립트가 브라우저에서 실제로 실행되는가"이므로
requests(HTML 파서·자바스크립트 엔진 없음)로는 확인할 수 없다.
팀 UI 테스트와 동일하게 Playwright로 실제 브라우저를 띄워 검증하며,
sec_browser 마커로 구분해 브라우저 없는 환경에서는 제외할 수 있다.
"""

import os
import uuid

import allure
import pytest

from config.settings import settings
from framework.api_security.pages.classroom_api import ClassroomApi
from framework.api_security.pages.dashboard_api import DashboardApi
from framework.api_security.pages.lxp_api import LxpApi
from utils.assertions import is_business_rejected, json_body


CLASSROOM_ID = settings.CLASSROOM_ID
STUDENT_ID = settings.STUDENT_ID
COURSE_ID = settings.COURSE_ID

# XSS 페이로드: 이미지 로드 실패를 유도해 onerror 핸들러를 실행시키는 형태
XSS_PAYLOAD = "<img src=x onerror=alert(1)>"

# 반사형 XSS 페이로드: 검색어에 그대로 실려 응답으로 되돌아오는지 확인
REFLECTED_PAYLOAD = "<script>alert(1)</script>"

# SQLi 페이로드: 항상 참인 조건을 덧붙여 쿼리 논리를 변형하려는 시도
SQLI_GET_PAYLOAD = f"{COURSE_ID} OR 1=1"
SQLI_POST_PAYLOAD = "a` OR `1`=`1"

# 이 서비스와 무관한 임의 출처 (허용되면 안 되는 Origin)
UNTRUSTED_ORIGIN = "https://evil.com"

# ID-38 브라우저 검증용
WEB_BASE_URL = "https://dev-qatrack-web.dev.elicer.io"

# 실행되면 안 되는 이벤트 핸들러 속성
EVENT_HANDLER_ATTRIBUTES = ("onerror", "onload", "onclick", "onmouseover")

# 렌더링 완료를 기다리는 시간 (ms) - 지연 실행되는 스크립트까지 포착
RENDER_WAIT_MS = 3000

# 게시글 본문이 렌더링되는 영역 (이 안만 검사해야 광고·애널리틱스 스크립트를 오탐하지 않음)
ARTICLE_CONTENT_ID = "boardArticleContent"

# DB·서버 내부 정보가 응답에 새어나왔는지 판별할 키워드
DB_LEAK_KEYWORDS = (
    "sql",
    "syntax",
    "psycopg",
    "sqlalchemy",
    "traceback",
    "postgres",
    "mysql",
)

# 브라우저 열람이 필요한 ID-38에서 참조할 게시글 (수동 검증 시 사용한 값)
STORED_XSS_ARTICLE_ID = os.getenv("SEC_STORED_XSS_ARTICLE_ID", "")


def _new_article_title(prefix):
    """실행마다 구분 가능한 제목 생성 (테스트가 만든 게시글임을 표시)"""
    return f"[SECTEST-{prefix}] {uuid.uuid4().hex[:8]}"


def _extract_article_id(response):
    """게시글 저장 응답에서 board_article_id 추출"""
    data = json_body(response)
    article_id = data.get("board_article_id")
    if article_id is None and isinstance(data.get("board_article"), dict):
        article_id = data["board_article"].get("id")
    assert article_id, f"게시글 id를 응답에서 찾지 못함 - BODY={response.text[:500]}"
    return article_id


@allure.epic("API 호출 보안성 테스트")
@allure.feature("인젝션(웹 취약점)")
@allure.label("owner", "yoodaewon")
@allure.label("team", "QA4")
@pytest.mark.sec_injection
class TestInjection:
    """인젝션 카테고리 보안 검증 (ID 37~42)"""

    # -- ID 37 ---------------------------------------------------------------
    @allure.title("ID-37 악성 스크립트 저장 시 무해화(XSS)")
    @pytest.mark.destructive
    @allure.label("tc_id", "37")
    @allure.label("priority", "P0")
    def test_id37_악성스크립트_저장_무해화(self, student_client):
        """게시글에 스크립트 태그를 저장한 뒤 재조회하여 이스케이프 여부 확인

        [기대] 재조회 시 content가 &lt;img ...&gt; 로 이스케이프되어 내려옴
        [실제] 원본 그대로 저장·반환 → 저장형 XSS의 씨앗이 남음 → FAIL(빨간불)

        서버가 입력을 무해한 문자로 바꾸지 않으면, 그 글을 여는 모든 사용자의
        브라우저가 태그를 '글자'가 아닌 '명령'으로 해석해 실행한다.
        """
        lxp = LxpApi(student_client)

        save_response = lxp.edit_board_article(
            classroom_id=CLASSROOM_ID,
            title=_new_article_title("XSS"),
            content=XSS_PAYLOAD,
        )
        article_id = _extract_article_id(save_response)

        read_response = lxp.get_board_article(article_id)
        saved_content = str(json_body(read_response))

        allure.attach(
            f"board_article_id={article_id}\n저장 요청 content={XSS_PAYLOAD}\n"
            f"조회 응답 일부={read_response.text[:800]}",
            name="게시글 저장·재조회 결과",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert XSS_PAYLOAD not in saved_content, (
            f"입력한 스크립트 태그가 무해화 없이 그대로 저장됨(board_article_id={article_id}) - "
            "게시글을 여는 사용자의 브라우저에서 실행되어 쿠키·세션 탈취 가능(저장형 XSS)"
        )

    # -- ID 38 ---------------------------------------------------------------
    @allure.title("ID-38 저장된 스크립트 실행(Stored XSS) 차단")
    @pytest.mark.sec_browser
    @allure.label("tc_id", "38")
    @allure.label("priority", "P0")
    def test_id38_저장된_스크립트_실행_차단(self, student_client, page):
        """저장된 XSS 페이로드가 브라우저에서 실행되는지 확인

        [기대] 게시글을 열어도 스크립트가 실행되지 않음
        [실제] alert 미발생 + onerror 속성 제거됨 → PASS

        ID-37이 저장 계층(서버가 무해화하는가)을 본다면 ID-38은 표현 계층
        (브라우저가 렌더링할 때 실행되는가)을 본다. 서버는 입력을 그대로
        저장하지만 프론트엔드가 렌더링 단계에서 이벤트 핸들러 속성을 제거해
        실행을 막는다. 다만 방어가 표현 계층에만 있어, 같은 데이터를 받는
        다른 클라이언트에는 보호가 적용되지 않을 수 있다.

        검증용 게시글은 이 테스트가 직접 만든다. 다른 테스트가 남긴 데이터에
        의존하면 실행 순서에 따라 결과가 달라진다.
        """
        # 1단계: 검증용 게시글 생성 (API)
        marker = uuid.uuid4().hex[:8]
        lxp = LxpApi(student_client)
        create_response = lxp.edit_board_article(
            classroom_id=CLASSROOM_ID,
            title=f"[SECTEST-XSS-BROWSER] {marker}",
            content=XSS_PAYLOAD,
        )

        article_id = _extract_article_id(create_response)

        target_url = f"{WEB_BASE_URL}/classrooms/{CLASSROOM_ID}/articles/{article_id}"
        allure.attach(
            f"게시글 id={article_id}\n저장 페이로드={XSS_PAYLOAD}\n주소={target_url}",
            name="검증용 게시글 생성",
            attachment_type=allure.attachment_type.TEXT,
        )

        # 2단계: 브라우저 로그인
        dialogs = []
        page.on("dialog", lambda dialog: (
            dialogs.append(dialog.message), dialog.dismiss()
        ))

        page.goto(f"{WEB_BASE_URL}/lxp")
        page.locator('input[name="loginId"]').fill(os.environ["ST_ID"])
        page.locator('input[name="password"]').fill(os.environ["ST_PW"])
        page.get_by_role("button", name="로그인").click()
        page.wait_for_url(f"{WEB_BASE_URL}/lxp", timeout=60_000)

        # 3단계: 게시글을 열고 렌더링 결과 확인
        page.goto(target_url)
        page.wait_for_timeout(RENDER_WAIT_MS)

        # 페이지 전체가 아니라 게시글 본문 영역만 검사한다.
        # 광고·애널리틱스 스크립트가 정상적으로 쓰는 onload 등을 오탐하지 않기 위함.
        content_area = page.locator(f"#{ARTICLE_CONTENT_ID}")
        content_html = (
            content_area.inner_html() if content_area.count() else page.content()
        )

        # 주입한 요소에 이벤트 핸들러가 실제로 붙어 있는지 DOM 속성으로 확인
        leaked_handlers = page.evaluate(
            """([containerId, attributes]) => {
                const root = document.getElementById(containerId) || document.body;
                const found = [];
                for (const element of root.querySelectorAll("*")) {
                    for (const attribute of attributes) {
                        if (element.hasAttribute(attribute)) {
                            found.push(`${element.tagName.toLowerCase()}[${attribute}]`);
                        }
                    }
                }
                return found;
            }""",
            [ARTICLE_CONTENT_ID, list(EVENT_HANDLER_ATTRIBUTES)],
        )

        allure.attach(
            f"발생한 대화상자={dialogs or '없음'}\n"
            f"본문 내 이벤트 핸들러={leaked_handlers or '없음'}\n\n"
            f"본문 HTML:\n{content_html[:1500]}",
            name="브라우저 렌더링 결과",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            page.screenshot(),
            name="게시글 화면",
            attachment_type=allure.attachment_type.PNG,
        )

        assert not dialogs, (
            f"저장된 스크립트가 브라우저에서 실행됨 - 대화상자 발생: {dialogs} "
            "(게시글을 여는 모든 사용자에게 스크립트가 실행되어 쿠키·세션 탈취 가능)"
        )
        assert not leaked_handlers, (
            f"게시글 본문에 이벤트 핸들러 속성이 남아 있음: {leaked_handlers} - "
            "지금은 실행되지 않아도 다른 경로로 발화할 여지가 있음"
        )

    # -- ID 39 ---------------------------------------------------------------
    @allure.title("ID-39 반사형 XSS를 통한 악성 스크립트 실행 차단")
    @allure.label("tc_id", "39")
    @allure.label("priority", "P0")
    def test_id39_반사형_XSS_차단(self, student_client):
        """검색어에 스크립트를 넣어 응답에 실행형으로 반사되는지 확인

        [기대] 200 + 빈 배열, Content-Type이 application/json이라 실행형 반사 없음
        JSON API는 응답이 HTML로 해석되지 않으므로 반사형 XSS가 성립하지 않는다.
        HTML로 응답하거나 페이로드가 그대로 실려 오면 반사형 XSS 위험이 있다.
        """
        classroom = ClassroomApi(student_client)
        response = classroom.get_articles(
            CLASSROOM_ID, skip=0, count=10, filter_title=REFLECTED_PAYLOAD
        )

        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type, (
            f"응답 Content-Type이 JSON이 아님({content_type}) - "
            "HTML로 해석되면 반사된 스크립트가 브라우저에서 실행될 수 있음"
        )

        assert REFLECTED_PAYLOAD not in response.text, (
            "검색어로 넣은 스크립트가 응답에 그대로 반사됨 - 반사형 XSS 위험"
        )

    # -- ID 40 ---------------------------------------------------------------
    @allure.title("ID-40 GET 요청값을 통한 악성 SQL 구문 삽입 차단")
    @allure.label("tc_id", "40")
    @allure.label("priority", "P0")
    def test_id40_GET_SQL_인젝션_차단(self, student_client):
        """정수 파라미터(course_id)에 SQL 구문을 넣어 타입 검증으로 차단되는지 확인

        [기대] 422 + int_parsing 에러, DB 에러·스택트레이스 미노출
        정수로 강제 파싱되므로 SQL 구문이 쿼리에 도달하기 전에 차단된다.
        """
        dashboard = DashboardApi(student_client)
        response = dashboard.get_student(STUDENT_ID, CLASSROOM_ID, SQLI_GET_PAYLOAD)

        assert is_business_rejected(response), (
            f"SQL 페이로드가 담긴 요청이 거부되지 않음 (status={response.status_code}) - "
            "입력값이 검증 없이 처리되어 쿼리에 도달할 위험"
        )

        body_lower = response.text.lower()
        leaked = [word for word in DB_LEAK_KEYWORDS if word in body_lower]
        assert not leaked, (
            f"응답에 DB·내부 오류 정보가 노출됨: {leaked} - "
            f"BODY={response.text[:500]}"
        )

    # -- ID 41 ---------------------------------------------------------------
    @allure.title("ID-41 POST 요청값을 통한 악성 SQL 구문 삽입 차단")
    @pytest.mark.destructive
    @allure.label("tc_id", "41")
    @allure.label("priority", "P0")
    def test_id41_POST_SQL_인젝션_차단(self, student_client):
        """게시글 제목에 SQL 페이로드를 저장한 뒤 재조회하여 실행 여부 확인

        [기대] 페이로드가 SQL로 실행되지 않고 평범한 문자열로 저장됨
        입력이 명령이 아닌 데이터로만 취급되어야 하며, 저장·조회 과정에서
        SQL이 실행되거나 데이터가 오염되면 안 된다.
        """
        lxp = LxpApi(student_client)

        save_response = lxp.edit_board_article(
            classroom_id=CLASSROOM_ID,
            title=SQLI_POST_PAYLOAD,
            content="x",
        )

        body_lower = save_response.text.lower()
        leaked = [word for word in DB_LEAK_KEYWORDS if word in body_lower]
        assert not leaked, (
            f"저장 요청 응답에 DB 오류 정보가 노출됨: {leaked} - "
            f"BODY={save_response.text[:500]}"
        )

        article_id = _extract_article_id(save_response)
        read_response = lxp.get_board_article(article_id)
        data = json_body(read_response)

        allure.attach(
            f"board_article_id={article_id}\n저장 요청 title={SQLI_POST_PAYLOAD}\n"
            f"조회 응답 일부={read_response.text[:800]}",
            name="SQL 페이로드 저장·재조회 결과",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert SQLI_POST_PAYLOAD in str(data), (
            "저장한 페이로드가 원본 문자열로 조회되지 않음 - "
            f"입력이 데이터가 아닌 구문으로 처리되었을 가능성(BODY={read_response.text[:500]})"
        )

    # -- ID 42 ---------------------------------------------------------------
    @allure.title("ID-42 외부 출처(CORS) 무제한 허용 차단")
    @allure.label("tc_id", "42")
    @allure.label("priority", "P0")
    def test_id42_CORS_임의출처_반사_차단(self, student_client):
        """임의 Origin으로 preflight 요청 시 허용 헤더에 그대로 반사되는지 확인

        [기대] Access-Control-Allow-Origin에 evil.com이 반사되지 않음
        [실제] 요청한 Origin을 그대로 반사 + credentials까지 허용 → FAIL(빨간불)

        [판정 근거] CORS는 서버가 요청을 거부하는 방식이 아니라 "이 출처를 허용한다"를
        헤더로 알려주고 실제 차단은 브라우저가 하는 구조다. 설정이 옳든 그르든
        상태코드는 200이고 본문은 비어 있으므로, 응답 헤더로만 판정한다.
        """
        classroom = ClassroomApi(student_client)
        response = classroom.options_preflight(CLASSROOM_ID, UNTRUSTED_ORIGIN)

        allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
        allow_credentials = response.headers.get("Access-Control-Allow-Credentials", "")

        allure.attach(
            f"요청 Origin={UNTRUSTED_ORIGIN}\n"
            f"Access-Control-Allow-Origin={allow_origin or '(없음)'}\n"
            f"Access-Control-Allow-Credentials={allow_credentials or '(없음)'}",
            name="CORS 응답 헤더",
            attachment_type=allure.attachment_type.TEXT,
        )

        assert allow_origin != UNTRUSTED_ORIGIN, (
            f"미허용 Origin({UNTRUSTED_ORIGIN})이 Access-Control-Allow-Origin에 그대로 반사됨"
            + (
                " + Access-Control-Allow-Credentials=true(인증정보 전송 허용) - "
                "로그인 사용자가 악성 사이트에 접속만 해도 그 사이트가 사용자의 "
                "인증정보로 API를 호출해 데이터 탈취 가능"
                if allow_credentials.lower() == "true"
                else " - 허용 출처를 화이트리스트로 지정해야 함"
            )
        )
