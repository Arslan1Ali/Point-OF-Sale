import flet as ft
from services.api import api_service

icons = ft.icons

class DashboardView(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.expand = True
        self.padding = 30
        
        # Stats Text Controls
        self.total_sales_text = ft.Text("$0.00", color="white", size=24, weight=ft.FontWeight.BOLD)
        self.orders_text = ft.Text("0", color="white", size=24, weight=ft.FontWeight.BOLD)
        self.customers_text = ft.Text("0", color="white", size=24, weight=ft.FontWeight.BOLD)
        self.inventory_text = ft.Text("0 Items", color="white", size=24, weight=ft.FontWeight.BOLD)

        self.recent_sales_list = ft.ListView(expand=True, spacing=10)

        self.content = ft.Column(
            [
                ft.Text("Dashboard", size=30, weight=ft.FontWeight.BOLD, color="white"),
                ft.Divider(height=20, color="transparent"),
                self._build_stats_row(),
                ft.Divider(height=30, color="transparent"),
                ft.Text("Recent Activity", size=20, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(
                    height=300,
                    bgcolor="#2d3033",
                    border_radius=10,
                    padding=10,
                    content=self.recent_sales_list
                )
            ],
            scroll=ft.ScrollMode.HIDDEN
        )
        self._load_data()

    def _load_data(self):
        stats = api_service.get_dashboard_stats()
        if stats:
            self.total_sales_text.value = stats.get("total_sales", "$0.00")
            self.orders_text.value = stats.get("orders", "0")
            self.customers_text.value = stats.get("customers", "0")
            self.inventory_text.value = stats.get("inventory", "0 Items")
            
            self.recent_sales_list.controls = []
            for sale in stats.get("recent_sales", []):
                self.recent_sales_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column([
                                    ft.Text(f"Order ID: {sale['id']}", color="white", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Date: {sale['created_at'][:10]}", color="grey", size=12),
                                ]),
                                ft.Text(f"${sale['total_amount']}", color="#03dac6", weight=ft.FontWeight.BOLD),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=10,
                        bgcolor="#1a1c1e",
                        border_radius=5
                    )
                )

            if self.page:
                self.page.update()

    def _build_stats_row(self):
        return ft.Row(
            [
                self._build_stat_card("Total Sales", self.total_sales_text, icons.ATTACH_MONEY, "#bb86fc"),
                self._build_stat_card("Orders", self.orders_text, icons.SHOPPING_CART, "#03dac6"),
                self._build_stat_card("Customers", self.customers_text, icons.PEOPLE, "#cf6679"),
                self._build_stat_card("Inventory", self.inventory_text, icons.INVENTORY_2, "#ffb74d"),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

    def _build_stat_card(self, title, value_control, icon, color):
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
                            value_control,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        expand=True
                    ),
                    ft.Icon(icon, color=color, size=40)
                ]
            )
        )
