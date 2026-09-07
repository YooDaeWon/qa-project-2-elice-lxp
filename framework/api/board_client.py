from config.settings import settings


def _multipart(payload):
    return [(key, (None, str(value))) for key, value in payload.items()]


class BoardClient:
    def __init__(self, api_client):
        self.api = api_client
        self.base = settings.API_BASE_URL.rstrip("/")
        self.classroom_base = settings.CLASSROOM_API_BASE_URL.rstrip("/")

    def classroom_articles(
        self,
        classroom_id,
        sort_by="created_desc",
        skip=0,
        count=10,
        filter_title=None,
    ):
        params = {
            "sort_by": sort_by,
            "skip": skip,
            "count": count,
        }
        if filter_title:
            params["filter_title"] = filter_title

        return self.api.get(
            f"{self.classroom_base}/classroom/{classroom_id}/article",
            params=params,
        )

    def article_get(self, org, board_article_id):
        return self.api.get(
            f"{self.base}/org/{org}/board/article/get/",
            params={"board_article_id": board_article_id},
        )

    def article_list(self, org, board_id, offset=0, count=20):
        return self.api.get(
            f"{self.base}/org/{org}/board/article/list/",
            params={
                "board_id": board_id,
                "offset": offset,
                "count": count,
            },
        )

    def article_edit(self, org, payload):
        return self.api.post(
            f"{self.base}/org/{org}/board/article/edit/",
            data=payload,
        )

    def article_delete(self, org, board_article_id):
        return self.api.post(
            f"{self.base}/org/{org}/board/article/delete/",
            files=_multipart({"board_article_id": board_article_id}),
        )

    def board_list(self, org, course_id):
        return self.api.get(
            f"{self.base}/org/{org}/board/list/",
            params={"course_id": course_id},
        )

    def board_edit(self, org, payload):
        return self.api.post(
            f"{self.base}/org/{org}/board/edit/",
            data=payload,
        )
