from playwright.sync_api import expect


class MainPage:
    """LXP 메인 페이지"""

    def __init__(self, page):
        self.page = page
        self.menu_button = page.get_by_role(
            "button",
            name="전체메뉴",
            exact=True,
        ).or_(
            page.locator("button:has(svg[data-testid='barsIcon'])")
        ).first
        self.menu_drawer = page.locator(
            '[class~="MuiDrawer-paper"]:visible'
        )
        self.menu_links = [
            self.menu_drawer.get_by_text("탐색", exact=True),
            self.menu_drawer.get_by_text("내 클래스", exact=True),
            self.menu_drawer.get_by_text("대시보드", exact=True),
        ]
        self.my_classes_link = page.get_by_role(
            "link",
            name="내 클래스",
            exact=True,
        )

    def verify_menu_button_visible(self):
        """햄버거 버튼 화면 표시 확인"""
        expect(self.menu_button).to_be_visible()

        box = self.menu_button.bounding_box()
        viewport = self.page.viewport_size
        assert box is not None
        assert viewport is not None
        assert box["x"] >= 0
        assert box["y"] >= 0
        assert box["x"] + box["width"] <= viewport["width"]
        assert box["y"] + box["height"] <= viewport["height"]

    def open_menu(self):
        """전체 메뉴 열기"""
        self.menu_button.click()

    def verify_menu_visible(self):
        """전체 메뉴 표시 확인"""
        for menu_link in self.menu_links:
            expect(menu_link).to_be_visible()

    def open_my_classes(self):
        """내 클래스 페이지 열기"""
        self.my_classes_link.click()
