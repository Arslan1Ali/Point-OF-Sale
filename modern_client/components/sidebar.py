import flet as ft
icons = ft.icons

class Sidebar(ft.Container):
    def __init__(self, app, page):
        super().__init__()
        self.app = app
        self.page = page
        self.width = 250
        self.bgcolor = "#2d3033"
        self.padding = 20
        self.content = self._build_content()

    def _build_content(self):
        return ft.Column(
            [
                ft.Text("Retail POS", size=24, weight=ft.FontWeight.BOLD, color="white"),
                ft.Divider(color="transparent", height=30),
                self._build_nav_item(icons.DASHBOARD, "Dashboard", "dashboard"),
                self._build_nav_item(icons.POINT_OF_SALE, "POS Terminal", "pos"),
                self._build_nav_item(icons.RECEIPT_LONG, "Orders", "orders"),
                self._build_nav_item(icons.INVENTORY, "Inventory", "inventory"),
                self._build_nav_item(icons.PEOPLE, "Customers", "customers"),
                ft.Divider(color="grey"),
                self._build_nav_item(icons.LOGOUT, "Logout", "logout", color="#cf6679"),
            ],
            spacing=10,
        )

    def _build_nav_item(self, icon, label, route, color="white"):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, color=color),
                    ft.Text(label, color=color, size=16),
                ],
                spacing=15,
            ),
            padding=15,
            border_radius=10,
            ink=True,
            on_click=lambda e: self.app.navigate(route),
            on_hover=lambda e: self._on_hover(e),
        )

    def _on_hover(self, e):
        e.control.bgcolor = "#3d4043" if e.data == "true" else None
        e.control.update()
