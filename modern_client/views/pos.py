import flet as ft
from services.api import api_service

icons = ft.icons

class POSView(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.expand = True
        self.padding = 20
        
        self.cart_items = []
        self.products = []
        self.customers = []
        self.selected_customer = None
        
        # UI Components
        self.product_grid = ft.GridView(
            expand=True,
            runs_count=4,
            max_extent=250,
            child_aspect_ratio=0.75,
            spacing=20,
            run_spacing=20,
        )
        self.cart_list = ft.ListView(expand=True, spacing=10)
        self.total_text = ft.Text("$0.00", size=24, weight=ft.FontWeight.BOLD, color="white")
        self.customer_dropdown = ft.Dropdown(
            label="Select Customer",
            hint_text="Guest Customer",
            width=350,
            options=[],
            on_change=self._on_customer_change,
            bgcolor="#2d3033",
            color="white",
            border_color="#bb86fc",
            text_style=ft.TextStyle(color="white"),
        )
        
        self.content = self._build_layout()
        # Defer data loading to after mount or call explicitly
        # For now, we call it here, but in Flet it's often better to use did_mount
        self._load_data()

    def _build_layout(self):
        return ft.Row(
            [
                # Left: Products
                ft.Container(
                    expand=3,
                    content=ft.Column(
                        [
                            self._build_header(),
                            self.product_grid
                        ]
                    )
                ),
                # Right: Cart
                ft.Container(
                    width=400,
                    bgcolor="#1a1c1e",
                    border=ft.border.only(left=ft.border.BorderSide(1, "#2d3033")),
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Text("Current Sale", size=24, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Container(height=10),
                            self.customer_dropdown,
                            ft.Divider(color="#2d3033"),
                            self.cart_list,
                            ft.Divider(color="#2d3033"),
                            ft.Row([ft.Text("Total", color="grey"), self.total_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Container(height=10),
                            ft.ElevatedButton(
                                "Checkout",
                                bgcolor="#bb86fc",
                                color="black",
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                height=50,
                                width=float("inf"),
                                on_click=self._checkout
                            )
                        ]
                    )
                )
            ],
            expand=True
        )

    def _build_header(self):
        return ft.Row(
            [
                ft.TextField(
                    hint_text="Search products...",
                    prefix_icon=icons.SEARCH,
                    bgcolor="#2d3033",
                    border_radius=10,
                    border_width=0,
                    color="white",
                    expand=True,
                    on_change=self._on_search
                ),
                ft.IconButton(icons.FILTER_LIST, icon_color="white", tooltip="Filter"),
                ft.IconButton(icons.REFRESH, icon_color="white", tooltip="Refresh", on_click=lambda e: self._load_data()),
            ]
        )

    def _load_data(self):
        self.products = api_service.get_products()
        self.customers = api_service.get_customers()
        
        self._render_products(self.products)
        
        self.customer_dropdown.options = [
            ft.dropdown.Option(key=c["id"], text=f"{c['first_name']} {c['last_name']}")
            for c in self.customers
        ]
        if self.page:
            self.page.update()

    def _render_products(self, products):
        self.product_grid.controls = [self._build_product_card(p) for p in products]
        if self.page:
            self.product_grid.update()

    def _on_search(self, e):
        query = e.control.value.lower()
        filtered = [p for p in self.products if query in p.get("name", "").lower()]
        self._render_products(filtered)

    def _build_product_card(self, product):
        name = product.get("name", "Unknown")
        price = float(product.get("retail_price", 0))
        color = "#bb86fc" 
        
        return ft.Container(
            bgcolor="#2d3033",
            border_radius=15,
            padding=15,
            ink=True,
            on_click=lambda e: self._add_to_cart(product),
            content=ft.Column(
                [
                    ft.Container(
                        height=100,
                        border_radius=10,
                        bgcolor=color, 
                        alignment=ft.alignment.center,
                        content=ft.Icon(icons.SHOPPING_BAG, color="white", size=40)
                    ),
                    ft.Text(name, size=16, weight=ft.FontWeight.BOLD, color="white", no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Row(
                        [
                            ft.Text(f"${price:.2f}", size=14, color="#bb86fc", weight=ft.FontWeight.BOLD),
                            ft.Container(
                                bgcolor="#bb86fc",
                                border_radius=50,
                                padding=5,
                                content=ft.Icon(icons.ADD, size=16, color="black")
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

    def _add_to_cart(self, product):
        price = float(product.get("retail_price", 0))
        existing = next((item for item in self.cart_items if item["id"] == product["id"]), None)
        if existing:
            existing["qty"] += 1
        else:
            self.cart_items.append({
                "id": product["id"],
                "name": product.get("name", "Unknown"),
                "price": price,
                "qty": 1
            })
        
        self._update_cart_ui()

    def _update_cart_ui(self):
        self.cart_list.controls = [self._build_cart_item(item) for item in self.cart_items]
        total = sum(item["price"] * item["qty"] for item in self.cart_items)
        self.total_text.value = f"${total:.2f}"
        if self.page:
            self.cart_list.update()
            self.total_text.update()

    def _build_cart_item(self, item):
        return ft.Container(
            bgcolor="#2d3033",
            padding=10,
            border_radius=10,
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(item["name"], color="white", weight=ft.FontWeight.BOLD, width=150, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"${item['price']:.2f}", color="grey", size=12),
                        ],
                    ),
                    ft.Row(
                        [
                            ft.IconButton(icons.REMOVE, icon_size=16, icon_color="white", on_click=lambda e: self._update_qty(item, -1)),
                            ft.Text(str(item["qty"]), color="white"),
                            ft.IconButton(icons.ADD, icon_size=16, icon_color="white", on_click=lambda e: self._update_qty(item, 1)),
                        ],
                        spacing=0
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

    def _update_qty(self, item, change):
        item["qty"] += change
        if item["qty"] <= 0:
            self.cart_items.remove(item)
        self._update_cart_ui()

    def _on_customer_change(self, e):
        self.selected_customer = e.control.value

    def _checkout(self, e):
        if not self.cart_items:
            return
            
        sale_data = {
            "customer_id": self.selected_customer,
            "currency": "USD",
            "lines": [
                {
                    "product_id": item["id"],
                    "quantity": item["qty"],
                    "unit_price": item["price"]
                }
                for item in self.cart_items
            ]
        }
        
        result = api_service.create_sale(sale_data)
        if result:
            self.cart_items = []
            self._update_cart_ui()
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Sale recorded successfully!")))
        else:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Failed to record sale.")))
