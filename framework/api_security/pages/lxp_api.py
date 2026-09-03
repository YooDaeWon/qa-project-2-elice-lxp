"""LXP(dev-qatrack-api) 보안 테스트 페이지 객체

LXP 서비스는 다른 호스트와 호출 규약이 다르다.
- 경로: /org/{org}/... 형태로 기관명이 URL에 포함된다
- 전송: POST + form-data (json이 아님)
- 응답: _result 봉투 구조 {"_result": {"status": "ok"|"fail", "status_code": 200}}
        실패 시 최상위에 fail_code가 함께 내려온다

form-data는 requests가 boundary를 자동 생성하도록 data= 로 전달한다.
(Content-Type을 수동 지정하면 boundary가 누락되어 요청이 깨진다)
"""

from config.settings import settings


class LxpApi:
    """LXP 서비스 액션 (시험 초기화·답안 제출 등)"""

    def __init__(self, api_client):
        self.api = api_client
        self.base = settings.API_BASE_URL.rstrip("/")
        self.org = settings.ORG

    def _org_url(self, path):
        """/org/{org}/{path} 형태의 LXP 전용 URL 생성"""
        return f"{self.base}/org/{self.org}/{path.lstrip('/')}"

    def reset_test_by_self(self, lecture_id):
        """학습자 스스로 시험 응시 상태를 초기화 (재응시 요청)

        재응시 횟수 제한이 서버에 있다면 일정 횟수 초과 시 거부되어야 한다.
        """
        return self.api.post(
            self._org_url("lecture/test/reset/by_self/"),
            data={"lecture_id": str(lecture_id)},
        )

    def add_quiz_response(self, material_quiz_id, answer):
        """시험 문항 답안 제출

        시험 시간이 종료된 뒤 호출하면 서버가 거부해야 한다.
        """
        return self.api.post(
            self._org_url("material_quiz/response/add/"),
            data={
                "material_quiz_id": str(material_quiz_id),
                "answer": answer,
            },
        )

    def edit_board_article(self, classroom_id, title, content, is_secret=False):
        """게시글 작성 (XSS·SQLi 페이로드 저장 시도용)

        저장 성공 시 응답에서 board_article_id를 받아 재조회에 사용한다.
        """
        return self.api.post(
            self._org_url("board/article/edit/"),
            data={
                "classroom_id": classroom_id,
                "title": title,
                "content": content,
                "is_secret": str(is_secret).lower(),
            },
        )

    def get_board_article(self, board_article_id):
        """게시글 단건 조회 (저장된 값이 어떻게 내려오는지 확인용)"""
        return self.api.get(
            self._org_url("board/article/get/"),
            params={"board_article_id": board_article_id},
        )
