import flet as ft
from services.api import api_service

class OrdersView(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.expand = True
        self.padding = 30
        
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Date")),
                ft.DataColumn(ft.Text("Customer")),
                ft.DataColumn(ft.Text("Total")),
                ft.DataColumn(ft.Text("Status")),
            ],
            rows=[],
            border=ft.border.all(1, "#2d3033"),
            vertical_lines=ft.border.BorderSide(1, "#2d3033"),
            horizontal_lines=ft.border.BorderSide(1, "#2d3033"),
            heading_row_color="#2d3033",
        )

        self.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Sales History", size=30, weight=ft.FontWeight.BOLD, color="white"),
                        ft.IconButton(ft.icons.REFRESH, icon_color="white", on_click=lambda e: self._load_data())
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(height=20, color="transparent"),
                ft.Container(
                    content=self.data_table,
                    expand=True,
                    bgcolor="#1a1c1e",
                    border_radius=10,
                )
            ],
            expand=True
        )
        self._load_data()

    def _load_data(self):
        sales = api_service.get_sales()
        self.data_table.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(sale["id"][:8] + "...", color="white")), # Truncate ID
                    ft.DataCell(ft.Text(sale["created_at"][:10], color="white")),
                    ft.DataCell(ft.Text(sale.get("customer_name", "Guest"), color="white")),
                    ft.DataCell(ft.Text(f"${float(sale['total_amount']):.2f}", color="#bb86fc")),
                    ft.DataCell(ft.Text("Completed", color="green")),
                ]
            ) for sale in sales
        ]
        if self.page:
            self.page.update()
