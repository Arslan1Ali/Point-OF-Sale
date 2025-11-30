import flet as ft
from views.login import LoginView
from views.dashboard import DashboardView
from views.pos import POSView
from views.orders import OrdersView
from views.inventory import InventoryView
from views.customers import CustomersView
from views.employees import EmployeesView
from views.returns import ReturnsView
from components.sidebar import Sidebar
from services.api import api_service

class ModernPOSApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        self._setup_error_handling()
        self.token = None
        self.current_view = None
        self.current_route = None
        self.main_layout = None
        self.content_area = None
        self.navigate("login")

    def _setup_error_handling(self):
        def on_error(message):
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message, color="white"),
                    bgcolor="#cf6679",
                    action="Dismiss",
                    action_color="white"
                )
            )
        api_service.set_error_handler(on_error)

    def setup_page(self):
        self.page.title = "Retail POS - Modern"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.bgcolor = "#1a1c1e"
        self.page.fonts = {
            "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf",
            "RobotoBold": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
        }
        self.page.theme = ft.Theme(font_family="Roboto")

    def login(self, token):
        self.token = token
        self.navigate("dashboard")

    def navigate(self, route):
        # Prevent redundant navigation
        if self.current_route == route:
            return
            
        self.current_route = route
        
        if route == "login":
            self.page.controls.clear()
            self.current_view = LoginView(self)
            self.page.add(self.current_view)
            self.page.update()
            return
            
        if route == "logout":
            self.token = None
            self.current_route = None
            self.navigate("login")
            return

        # Authenticated Routes
        if not self.token:
            self.current_route = None
            self.navigate("login")
            return

        # Create Main Layout if it doesn't exist
        if not self.content_area:
            self.content_area = ft.Container(expand=True, bgcolor="#1a1c1e")
            self.main_layout = ft.Row(
                [
                    Sidebar(self, self.page),
                    ft.VerticalDivider(width=1, color="#2d3033"),
                    self.content_area
                ],
                expand=True,
                spacing=0
            )

        # Select View
        if route == "dashboard":
            content = DashboardView(self)
        elif route == "pos":
            content = POSView(self)
        elif route == "orders":
            content = OrdersView(self)
        elif route == "inventory":
            content = InventoryView(self)
        elif route == "customers":
            content = CustomersView(self)
        elif route == "employees":
            content = EmployeesView(self)
        elif route == "returns":
            content = ReturnsView(self)
        else:
            content = ft.Container(alignment=ft.alignment.center, content=ft.Text(f"{route.capitalize()} Coming Soon", size=30))

        # Update Content
        self.content_area.content = content
        
        # Ensure Main Layout is displayed
        if self.main_layout not in self.page.controls:
            self.page.controls.clear()
            self.page.add(self.main_layout)
        
        self.page.update()

def main(page: ft.Page):
    app = ModernPOSApp(page)

if __name__ == "__main__":
    ft.app(target=main)
