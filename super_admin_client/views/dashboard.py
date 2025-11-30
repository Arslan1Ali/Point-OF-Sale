import flet as ft
from services.api import api_client

class DashboardView(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.expand = True
        self.padding = 20
        
        self.tenants_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Domain")),
                ft.DataColumn(ft.Text("Plan ID")),
                ft.DataColumn(ft.Text("Status")),
            ],
            rows=[]
        )
        
        self.plans_container = ft.Row(wrap=True, spacing=20)

        self.content = ft.Column(
            [
                ft.Row([
                    ft.Text("SuperAdmin Dashboard", size=30, weight="bold"),
                    ft.IconButton(ft.icons.REFRESH, on_click=self._refresh_data)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Row(
                    [
                        self._build_card("Tenants", "0", ft.icons.BUSINESS),
                        self._build_card("Total Revenue", "$0.00", ft.icons.MONEY),
                        self._build_card("System Health", "Good", ft.icons.HEALTH_AND_SAFETY),
                    ]
                ),
                ft.Container(height=20),
                ft.Text("Subscription Plans", size=20, weight="bold"),
                self.plans_container,
                ft.Container(height=20),
                ft.Row([
                    ft.Text("Tenant Management", size=20, weight="bold"),
                    ft.ElevatedButton("Create Tenant", icon=ft.icons.ADD, on_click=self._open_create_dialog)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.tenants_table
            ],
            scroll=ft.ScrollMode.AUTO
        )
        
        # Create Tenant Dialog Components
        self.new_tenant_name = ft.TextField(label="Tenant Name")
        self.new_tenant_domain = ft.TextField(label="Custom Domain (Optional)")
        self.plan_dropdown = ft.Dropdown(label="Select Plan", options=[])
        self.create_dialog = ft.AlertDialog(
            title=ft.Text("Create New Tenant"),
            content=ft.Column([
                self.new_tenant_name,
                self.new_tenant_domain,
                self.plan_dropdown
            ], height=200),
            actions=[
                ft.TextButton("Cancel", on_click=self._close_create_dialog),
                ft.ElevatedButton("Create", on_click=self._create_tenant)
            ]
        )

    def did_mount(self):
        self._refresh_data(None)

    def _refresh_data(self, e):
        # Fetch Plans
        plans = api_client.get_plans()
        self.plans_container.controls = [
            self._build_plan_card(p) for p in plans
        ]
        
        # Update Dropdown
        self.plan_dropdown.options = [
            ft.dropdown.Option(key=p['id'], text=f"{p['name']} (${p['price']})") for p in plans
        ]

        # Fetch Tenants
        tenants = api_client.get_tenants()
        self.tenants_table.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(t['name'])),
                    ft.DataCell(ft.Text(t['domain'] or "-")),
                    ft.DataCell(ft.Text(t['subscription_plan_id'])), # TODO: Resolve name
                    ft.DataCell(ft.Text("Active" if t['active'] else "Inactive", color="green" if t['active'] else "red")),
                ]
            ) for t in tenants
        ]
        self.update()

    def _build_plan_card(self, plan):
        return ft.Container(
            width=250,
            padding=15,
            bgcolor="#2d3033",
            border_radius=10,
            content=ft.Column([
                ft.Text(plan['name'], size=18, weight="bold"),
                ft.Text(f"${plan['price']}", size=24, color="green"),
                ft.Text(f"{plan['duration_months']} Months", size=12, italic=True),
                ft.Text(plan['description'] or "", size=12),
            ])
        )

    def _open_create_dialog(self, e):
        self.app.page.dialog = self.create_dialog
        self.create_dialog.open = True
        self.app.page.update()

    def _close_create_dialog(self, e):
        self.create_dialog.open = False
        self.app.page.update()

    def _create_tenant(self, e):
        if not self.new_tenant_name.value or not self.plan_dropdown.value:
            return # Validation
            
        res = api_client.create_tenant(
            name=self.new_tenant_name.value,
            subscription_plan_id=self.plan_dropdown.value,
            domain=self.new_tenant_domain.value
        )
        
        if res:
            self._close_create_dialog(None)
            self._refresh_data(None)
            self.new_tenant_name.value = ""
            self.new_tenant_domain.value = ""
            self.plan_dropdown.value = None

    def _build_card(self, title, value, icon):
        return ft.Container(
            width=200,
            height=100,
            bgcolor="#2d3033",
            border_radius=10,
            padding=10,
            content=ft.Column(
                [
                    ft.Icon(icon),
                    ft.Text(title, size=12, color="grey"),
                    ft.Text(value, size=20, weight="bold")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
