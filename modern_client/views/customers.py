import flet as ft
from services.api import api_service

icons = ft.icons

class CustomersView(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.expand = True
        self.padding = 20
        self.customers = []
        
        # UI Components
        self.search_field = ft.TextField(
            hint_text="Search customers...",
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
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Phone")),
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
                        ft.Text("Customer Management", size=28, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Add Customer",
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
            
        self.customers = api_service.get_customers(search=search, active=active)
        self._render_table()

    def _render_table(self):
        self.data_table.rows = []
        for c in self.customers:
            full_name = f"{c.get('first_name', '')} {c.get('last_name', '')}"
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(full_name, color="white")),
                        ft.DataCell(ft.Text(c.get("email", ""), color="white")),
                        ft.DataCell(ft.Text(c.get("phone") or "-", color="white")),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.IconButton(icons.EDIT, icon_color="blue", on_click=lambda e, c=c: self._open_edit_dialog(c)),
                                    ft.IconButton(icons.DELETE, icon_color="red", on_click=lambda e, c=c: self._delete_customer(c)),
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
        self.dialog_title = "Add Customer"
        self.current_customer = None
        self._open_dialog()

    def _open_edit_dialog(self, customer):
        self.dialog_title = "Edit Customer"
        self.current_customer = customer
        self._open_dialog()

    def _open_dialog(self):
        self.first_name_field = ft.TextField(label="First Name", value=self.current_customer.get("first_name") if self.current_customer else "")
        self.last_name_field = ft.TextField(label="Last Name", value=self.current_customer.get("last_name") if self.current_customer else "")
        self.email_field = ft.TextField(label="Email", value=self.current_customer.get("email") if self.current_customer else "")
        self.phone_field = ft.TextField(label="Phone", value=self.current_customer.get("phone") if self.current_customer else "")

        self.dialog = ft.AlertDialog(
            title=ft.Text(self.dialog_title),
            content=ft.Column(
                [
                    self.first_name_field,
                    self.last_name_field,
                    self.email_field,
                    self.phone_field
                ],
                tight=True,
                width=400
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.close_dialog()),
                ft.ElevatedButton("Save", on_click=self._save_customer)
            ],
        )
        self.page.show_dialog(self.dialog)

    def _save_customer(self, e):
        data = {
            "first_name": self.first_name_field.value,
            "last_name": self.last_name_field.value,
            "email": self.email_field.value,
            "phone": self.phone_field.value or None
        }

        if self.current_customer:
            # Update
            data["expected_version"] = self.current_customer["version"]
            result = api_service.update_customer(self.current_customer["id"], data)
        else:
            # Create
            result = api_service.create_customer(data)

        if result:
            self.page.close_dialog()
            self._load_data()
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Customer saved!")))
        else:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Error saving customer")))

    def _delete_customer(self, customer):
        if api_service.delete_customer(customer["id"], customer["version"]):
            self._load_data()
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Customer deleted")))
        else:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Error deleting customer")))
