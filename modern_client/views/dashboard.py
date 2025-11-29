import flet as ft
icons = ft.icons

class DashboardView(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.expand = True
        self.padding = 30
        self.content = ft.Column(
            [
                ft.Text("Dashboard", size=30, weight=ft.FontWeight.BOLD, color="white"),
                ft.Divider(height=20, color="transparent"),
                self._build_stats_row(),
                ft.Divider(height=30, color="transparent"),
                ft.Text("Recent Activity", size=20, weight=ft.FontWeight.BOLD, color="white"),
                # Placeholder for charts/tables
                ft.Container(
                    height=300,
                    bgcolor="#2d3033",
                    border_radius=10,
                    alignment=ft.alignment.center,
                    content=ft.Text("Sales Chart Placeholder", color="grey")
                )
            ],
            scroll=ft.ScrollMode.AUTO
        )

    def _build_stats_row(self):
        return ft.Row(
            [
                self._build_stat_card("Total Sales", "$12,450", icons.ATTACH_MONEY, "#bb86fc"),
                self._build_stat_card("Orders", "156", icons.SHOPPING_CART, "#03dac6"),
                self._build_stat_card("Customers", "1,203", icons.PEOPLE, "#cf6679"),
                self._build_stat_card("Inventory", "458 Items", icons.INVENTORY_2, "#ffb74d"),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

    def _build_stat_card(self, title, value, icon, color):
        return ft.Container(
            width=250,
            height=120,
            bgcolor="#2d3033",
            border_radius=15,
            padding=20,
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(title, color="grey", size=14),
                            ft.Text(value, color="white", size=24, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        expand=True
                    ),
                    ft.Icon(icon, color=color, size=40)
                ]
            )
        )
