import flet as ft
from services.api import api_service

icons = ft.icons

class ReturnsView(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.expand = True
        self.padding = 20
        self.current_sale = None
        
        # UI Components
        self.order_id_field = ft.TextField(
            label="Order ID",
            hint_text="Enter Sale ID to return items",
            bgcolor="#2d3033",
            border_radius=10,
            border_width=0,
            color="white",
            expand=True,
            on_submit=self._search_order
        )
        
        self.search_btn = ft.IconButton(
            icon=icons.SEARCH,
            icon_color="#bb86fc",
            bgcolor="#2d3033",
            on_click=self._search_order
        )

        self.items_list = ft.ListView(expand=True, spacing=10)
        self.return_btn = ft.ElevatedButton(
            "Process Return",
            bgcolor="#cf6679",
            color="white",
            on_click=self._process_return,
            visible=False
        )

        self.returns_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Return ID")),
                ft.DataColumn(ft.Text("Order ID")),
                ft.DataColumn(ft.Text("Date")),
                ft.DataColumn(ft.Text("Refund Amount")),
            ],
            rows=[],
            heading_row_color="#2d3033",
            data_row_color={"hovered": "#2d3033"},
            expand=True,
        )

        self.content = self._build_layout()
        self._load_returns()

    def _build_layout(self):
        return ft.Column(
            [
                ft.Text("Returns Management", size=28, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(height=20),
                ft.Row([self.order_id_field, self.search_btn]),
                ft.Container(height=20),
                ft.Text("Order Items", size=20, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(
                    content=self.items_list,
                    height=200, # Fixed height for items list
                    bgcolor="#1a1c1e",
                    border_radius=10,
                    padding=10
                ),
                ft.Container(height=10),
                ft.Row([self.return_btn], alignment=ft.MainAxisAlignment.END),
                ft.Divider(height=30, color="grey"),
                ft.Text("Recent Returns", size=20, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(
                    content=self.returns_table,
                    expand=True,
                    bgcolor="#1a1c1e",
                    border_radius=10,
                )
            ],
            expand=True
        )

    def _load_returns(self):
        returns = api_service.get_returns()
        self.returns_table.rows = []
        for r in returns:
            self.returns_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(r.get("id", "")[:8] + "...", color="white", tooltip=r.get("id"))),
                        ft.DataCell(ft.Text(r.get("sale_id", "")[:8] + "...", color="white", tooltip=r.get("sale_id"))),
                        ft.DataCell(ft.Text(r.get("created_at", "")[:10], color="white")),
                        ft.DataCell(ft.Text(f"${r.get('total_amount', '0.00')}", color="#cf6679", weight=ft.FontWeight.BOLD)),
                    ]
                )
            )
        if self.page:
            self.page.update()

    def _search_order(self, e):
        sale_id = self.order_id_field.value
        if not sale_id:
            return

        sale = api_service.get_sale(sale_id)
        if sale:
            self.current_sale = sale
            self._render_items()
            self.return_btn.visible = True
            self.page.update()
        else:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Order not found")))

    def _render_items(self):
        self.items_list.controls = []
        self.return_quantities = {} # Map sale_item_id -> TextField

        if not self.current_sale or "items" not in self.current_sale:
            return

        for item in self.current_sale["items"]:
            qty_sold = item.get("quantity", 0)
            qty_returned = item.get("returned_quantity", 0)
            qty_remaining = qty_sold - qty_returned
            
            qty_field = ft.TextField(
                value="0",
                width=100,
                label="Return Qty",
                keyboard_type=ft.KeyboardType.NUMBER,
                bgcolor="#2d3033",
                color="white",
                border_color="#bb86fc",
                disabled=(qty_remaining <= 0)
            )
            self.return_quantities[item["id"]] = qty_field

            self.items_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column([
                                ft.Text(f"Product ID: {item['product_id']}", color="white", weight=ft.FontWeight.BOLD),
                                ft.Text(f"Sold Price: ${item['unit_price']}", color="grey"),
                            ], expand=True),
                            ft.Column([
                                ft.Text(f"Sold: {qty_sold}", color="white"),
                                ft.Text(f"Returned: {qty_returned}", color="#cf6679"),
                                ft.Text(f"Remaining: {qty_remaining}", color="#03dac6", weight=ft.FontWeight.BOLD),
                            ]),
                            qty_field
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=10,
                    bgcolor="#2d3033",
                    border_radius=5
                )
            )

    def _process_return(self, e):
        if not self.current_sale:
            return

        lines = []
        for item_id, field in self.return_quantities.items():
            try:
                qty = int(field.value)
                if qty > 0:
                    # Find the item to check limits
                    item_data = next((i for i in self.current_sale["items"] if i["id"] == item_id), None)
                    if item_data:
                        qty_sold = item_data.get("quantity", 0)
                        qty_returned = item_data.get("returned_quantity", 0)
                        qty_remaining = qty_sold - qty_returned
                        
                        if qty > qty_remaining:
                            self.page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Error: Cannot return {qty} for item {item_id}. Only {qty_remaining} remaining.")))
                            return

                    lines.append({
                        "sale_item_id": item_id,
                        "quantity": qty
                    })
            except ValueError:
                pass

        if not lines:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("No items selected for return")))
            return

        payload = {
            "sale_id": self.current_sale["id"],
            "lines": lines
        }

        result = api_service.create_return(payload)
        if result:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Return processed successfully!")))
            self.current_sale = None
            self.items_list.controls = []
            self.return_btn.visible = False
            self.order_id_field.value = ""
            self._load_returns() # Refresh the list
            self.page.update()
        else:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Error processing return")))
