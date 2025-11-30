import flet as ft
from services.api import api_service

icons = ft.icons

class UsersView(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.expand = True
        self.padding = 20
        self.users = []
        
        # UI Components
        self.search_field = ft.TextField(
            hint_text="Search users (email)...",
            prefix_icon=icons.SEARCH,
            bgcolor="#2d3033",
            border_radius=10,
            border_width=0,
            color="white",
            expand=True,
            on_change=self._on_search
        )

        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Role")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[],
            heading_row_color="#2d3033",
            data_row_color={"hovered": "#2d3033"},
        )

        self.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Cashier Management", size=24, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Add Cashier",
                            icon=icons.ADD,
                            bgcolor="#bb86fc",
                            color="black",
                            on_click=self._open_add_cashier_dialog
                        ),
                        ft.IconButton(icons.REFRESH, icon_color="white", on_click=lambda e: self._load_data())
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Container(height=20),
                ft.Row([self.search_field]),
                ft.Container(height=20),
                ft.Container(
                    content=self.data_table,
                    bgcolor="#1a1c1e",
                    border_radius=10,
                    padding=10,
                )
            ],
            expand=True,
            scroll=ft.ScrollMode.HIDDEN
        )
        
        self._load_data()

    def _load_data(self, search=None):
        # Filter to show only Cashiers
        self.users = api_service.get_users(search=search, role="CASHIER")
        self._render_table()

    def _open_add_cashier_dialog(self, e):
        from datetime import datetime
        
        first_name = ft.TextField(label="First Name", bgcolor="#2d3033", color="white", border_color="#bb86fc", width=300)
        last_name = ft.TextField(label="Last Name", bgcolor="#2d3033", color="white", border_color="#bb86fc", width=300)
        email = ft.TextField(label="Email", bgcolor="#2d3033", color="white", border_color="#bb86fc", width=300)
        password = ft.TextField(label="Password", password=True, can_reveal_password=True, bgcolor="#2d3033", color="white", border_color="#bb86fc", width=300)
        
        def save(e):
            if not all([first_name.value, last_name.value, email.value, password.value]):
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("All fields are required")))
                return
                
            data = {
                "first_name": first_name.value,
                "last_name": last_name.value,
                "email": email.value,
                "position": "Cashier",
                "hire_date": datetime.now().strftime('%Y-%m-%d'),
                "base_salary": 0, # Default or prompt?
                "create_user_account": True,
                "password": password.value,
                "role": "CASHIER"
            }
            
            if api_service.create_employee(data):
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Cashier created successfully!")))
                dlg.open = False
                self._load_data()
                self.page.update()
            else:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Error creating cashier")))

        dlg = ft.AlertDialog(
            title=ft.Text("Add New Cashier"),
            content=ft.Column(
                [first_name, last_name, email, password],
                tight=True,
                height=300,
                width=350
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dlg, 'open', False)),
                ft.ElevatedButton("Create", on_click=save, bgcolor="#bb86fc", color="black"),
            ],
            bgcolor="#1a1c1e",
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _render_table(self):
        self.data_table.rows = []
        for user in self.users:
            status_color = "#03dac6" if user["active"] else "#cf6679"
            status_text = "Active" if user["active"] else "Inactive"
            
            actions = [
                ft.IconButton(
                    icon=icons.LOCK_RESET, 
                    icon_color="#ffb74d", 
                    tooltip="Reset Password",
                    on_click=lambda e, u=user: self._open_password_dialog(u)
                )
            ]
            
            if user["active"]:
                actions.append(
                    ft.IconButton(
                        icon=icons.BLOCK, 
                        icon_color="#cf6679", 
                        tooltip="Deactivate",
                        on_click=lambda e, u=user: self._toggle_status(u)
                    )
                )
            else:
                actions.append(
                    ft.IconButton(
                        icon=icons.CHECK_CIRCLE, 
                        icon_color="#03dac6", 
                        tooltip="Activate",
                        on_click=lambda e, u=user: self._toggle_status(u)
                    )
                )

            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(user['email'], color="white")),
                        ft.DataCell(ft.Text(user['role'], color="white")),
                        ft.DataCell(ft.Container(
                            content=ft.Text(status_text, color="black", size=12),
                            bgcolor=status_color,
                            padding=5,
                            border_radius=5
                        )),
                        ft.DataCell(ft.Row(actions)),
                    ]
                )
            )
        if self.page:
            self.page.update()

    def _on_search(self, e):
        self._load_data(search=e.control.value)

    def _open_password_dialog(self, user):
        new_password = ft.TextField(
            label="New Password", 
            password=True, 
            can_reveal_password=True, 
            bgcolor="#2d3033", 
            color="white", 
            border_color="#bb86fc", 
            width=300
        )

        def save(e):
            if not new_password.value or len(new_password.value) < 8:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Password must be at least 8 characters")))
                return

            if api_service.reset_user_password(user['id'], new_password.value, user['version']):
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Password reset successfully!")))
                dlg.open = False
                self._load_data()
                self.page.update()
            else:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Error resetting password")))

        dlg = ft.AlertDialog(
            title=ft.Text(f"Reset Password for {user['email']}"),
            content=new_password,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dlg, 'open', False)),
                ft.ElevatedButton("Reset", on_click=save, bgcolor="#cf6679", color="white"),
            ],
            bgcolor="#1a1c1e",
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _toggle_status(self, user):
        success = False
        if user['active']:
            success = api_service.deactivate_user(user['id'], user['version'])
            msg = "User deactivated"
        else:
            success = api_service.activate_user(user['id'], user['version'])
            msg = "User activated"
            
        if success:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text(msg)))
            self._load_data()
        else:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Error changing status")))
