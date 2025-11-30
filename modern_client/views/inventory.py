import flet as ft
from services.api import api_service

icons = ft.icons

class InventoryView(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.expand = True
        self.padding = 20
        self.products = []
        
        # UI Components
        self.search_field = ft.TextField(
            hint_text="Search inventory...",
            prefix_icon=icons.SEARCH,
            bgcolor="#2d3033",
            border_radius=10,
            border_width=0,
            color="white",
            expand=True,
            on_change=self._on_search
        )

        self.filter_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("All"),
                ft.dropdown.Option("Active"),
                ft.dropdown.Option("Inactive"),
            ],
            value="Active",
            width=150,
            bgcolor="#2d3033",
            color="white",
            border_color="#bb86fc",
            on_change=self._on_filter_change
        )
        
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("SKU")),
                ft.DataColumn(ft.Text("Price")),
                ft.DataColumn(ft.Text("Stock")), # Placeholder, backend doesn't send stock in list yet
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[],
            heading_row_color="#2d3033",
            data_row_color={"hovered": "#2d3033"},
            expand=True,
        )

        self.content = self._build_layout()
        self._load_data()

    def _build_layout(self):
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Inventory Management", size=28, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Add Product",
                            icon=icons.ADD,
                            bgcolor="#bb86fc",
                            color="black",
                            on_click=self._open_add_dialog
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Container(height=20),
                ft.Row([self.search_field, self.filter_dropdown]),
                ft.Container(height=20),
                ft.Container(
                    content=self.data_table,
                    expand=True,
                    bgcolor="#1a1c1e",
                    border_radius=10,
                )
            ],
            expand=True
        )

    def _load_data(self, search=None):
        active = None
        if self.filter_dropdown.value == "Active":
            active = True
        elif self.filter_dropdown.value == "Inactive":
            active = False
            
        self.products = api_service.get_products(search=search, active=active)
        self._render_table()

    def _render_table(self):
        self.data_table.rows = []
        for p in self.products:
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(p.get("name", ""), color="white")),
                        ft.DataCell(ft.Text(p.get("sku", ""), color="white")),
                        ft.DataCell(ft.Text(f"${p.get('retail_price', '0.00')}", color="#bb86fc")),
                        ft.DataCell(ft.Text("-", color="grey")), # Stock not in list response
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.IconButton(icons.EDIT, icon_color="blue", on_click=lambda e, p=p: self._open_edit_dialog(p)),
                                    ft.IconButton(icons.DELETE, icon_color="red", on_click=lambda e, p=p: self._delete_product(p)),
                                ]
                            )
                        ),
                    ]
                )
            )
        if self.page:
            self.page.update()

    def _on_search(self, e):
        self._load_data(search=e.control.value)

    def _on_filter_change(self, e):
        self._load_data(search=self.search_field.value)

    def _open_add_dialog(self, e):
        self.dialog_title = "Add Product"
        self.current_product = None
        self._open_dialog()

    def _open_edit_dialog(self, product):
        self.dialog_title = "Edit Product"
        self.current_product = product
        self._open_dialog()

    def _open_dialog(self):
        self.name_field = ft.TextField(label="Name", value=self.current_product.get("name") if self.current_product else "")
        self.sku_field = ft.TextField(label="SKU", value=self.current_product.get("sku") if self.current_product else "")
        self.price_field = ft.TextField(label="Retail Price", value=str(self.current_product.get("retail_price")) if self.current_product else "0.00")
        self.cost_field = ft.TextField(label="Purchase Price", value=str(self.current_product.get("purchase_price")) if self.current_product else "0.00")

        fields = [
            self.name_field,
            self.sku_field,
            self.price_field,
            self.cost_field
        ]

        if not self.current_product:
            self.stock_field = ft.TextField(label="Initial Stock", value="0")
            fields.append(self.stock_field)
        else:
            self.stock_field = None

        self.dialog = ft.AlertDialog(
            title=ft.Text(self.dialog_title),
            content=ft.Column(
                fields,
                tight=True,
                width=400
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close_dialog()),
                ft.ElevatedButton("Save", on_click=self._save_product)
            ],
        )
        self.page.show_dialog(self.dialog)

    def _save_product(self, e):
        try:
            data = {
                "name": self.name_field.value,
                "sku": self.sku_field.value,
                "retail_price": float(self.price_field.value),
                "purchase_price": float(self.cost_field.value),
                "currency": "USD"
            }

            if self.current_product:
                # Update
                data["expected_version"] = self.current_product["version"]
                result = api_service.update_product(self.current_product["id"], data)
            else:
                # Create
                result = api_service.create_product(data)
                if result and self.stock_field:
                    try:
                        initial_stock = int(self.stock_field.value)
                        if initial_stock > 0:
                            api_service.record_inventory_movement(result["id"], initial_stock)
                    except ValueError:
                        pass # Ignore invalid stock value

            if result:
                self.page.close_dialog()
                self._load_data()
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Product saved!")))
            else:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Error saving product")))
        except ValueError:
             self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Invalid number format")))

    def _delete_product(self, product):
        if api_service.delete_product(product["id"], product["version"]):
            self._load_data()
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Product deleted")))
        else:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Error deleting product")))
