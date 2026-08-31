class MainPage:
    """LXP 메인 페이지"""

    def __init__(self, page):
        self.page = page
        self.my_classes_link = page.get_by_role(
            "link",
            name="내 클래스",
            exact=True,
        )

    def open_my_classes(self):
        """내 클래스 페이지 열기"""
        self.my_classes_link.click()
