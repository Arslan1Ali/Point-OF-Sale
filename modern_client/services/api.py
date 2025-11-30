import httpx
import os
from config import settings

class ApiService:
    def __init__(self):
        self.token = None
        self.client = httpx.Client(base_url=settings.API_BASE_URL, timeout=10.0)
        self.error_handler = None

    def set_error_handler(self, handler):
        self.error_handler = handler

    def _handle_error(self, context, error):
        message = f"{context}: {str(error)}"
        print(message)
        if self.error_handler:
            self.error_handler(message)

    def set_token(self, token):
        self.token = token
        self.client.headers["Authorization"] = f"Bearer {token}"

    def login(self, email, password):
        print(f"DEBUG: Attempting login for {email} at /auth/login")
        try:
            # Backend expects JSON payload at /auth/login
            response = self.client.post("/auth/login", json={"email": email, "password": password})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Login failed", e)
            return None

    def get_products(self, search=None, category_id=None, active=None, limit=100):
        try:
            params = {"limit": limit}
            if search: params["search"] = search
            if category_id: params["category_id"] = category_id
            if active is not None: params["active"] = str(active).lower()
            
            response = self.client.get("/products", params=params)
            response.raise_for_status()
            return response.json()["items"]
        except httpx.HTTPError as e:
            self._handle_error("Fetch products failed", e)
            return []

    def get_dashboard_stats(self):
        try:
            stats = {
                "total_sales": "$0.00",
                "orders": "0",
                "customers": "0",
                "inventory": "0 Items",
                "recent_sales": []
            }
            
            # Get Inventory Count
            resp_prod = self.client.get("/products", params={"limit": 1})
            if resp_prod.status_code == 200:
                data = resp_prod.json()
                stats["inventory"] = f"{data.get('meta', {}).get('total', 0)} Items"

            # Get Customers Count
            resp_cust = self.client.get("/customers", params={"limit": 1})
            if resp_cust.status_code == 200:
                data = resp_cust.json()
                stats["customers"] = str(data.get('meta', {}).get('total', 0))

            # Get Sales/Orders Count and Estimate Total
            resp_sales = self.client.get("/sales", params={"limit": 100}) # Fetch last 100 for sum
            if resp_sales.status_code == 200:
                data = resp_sales.json()
                total_count = data.get('meta', {}).get('total', 0)
                stats["orders"] = str(total_count)
                
                # Calculate sum from the fetched items (approximate if > 100)
                items = data.get("items", [])
                total_amount = sum(float(s.get("total_amount", 0)) for s in items)
                stats["total_sales"] = f"${total_amount:,.2f}"
                
                # Recent Sales (Top 5)
                stats["recent_sales"] = items[:5]

            return stats
        except Exception as e:
            print(f"Error fetching dashboard stats: {e}")
            return None

    def create_product(self, product_data):
        try:
            response = self.client.post("/products", json=product_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Create product failed", e)
            return None

    def update_product(self, product_id, product_data):
        try:
            response = self.client.patch(f"/products/{product_id}", json=product_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Update product failed", e)
            return None

    def delete_product(self, product_id, version):
        print(f"DEBUG: delete_product called for {product_id}")
        try:
            # Backend requires expected_version for deactivation/deletion
            # Use deactivate endpoint instead of DELETE
            response = self.client.post(f"/products/{product_id}/deactivate", json={"expected_version": version})
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            self._handle_error("Delete product failed", e)
            return False

    def record_inventory_movement(self, product_id: str, quantity: int, reason: str = "Initial Stock") -> dict | None:
        try:
            response = self.client.post(
                f"/inventory/products/{product_id}/movements",
                json={
                    "quantity": quantity,
                    "direction": "in",
                    "reason": reason
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Record inventory movement failed", e)
            return None

    def get_customers(self, search=None, active=None, limit=100):
        try:
            params = {"limit": limit}
            if search: params["search"] = search
            if active is not None: params["active"] = str(active).lower()

            response = self.client.get("/customers", params=params)
            response.raise_for_status()
            return response.json()["items"]
        except httpx.HTTPError as e:
            self._handle_error("Fetch customers failed", e)
            return []

    def create_customer(self, customer_data):
        try:
            response = self.client.post("/customers", json=customer_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Create customer failed", e)
            return None

    def update_customer(self, customer_id, customer_data):
        try:
            response = self.client.patch(f"/customers/{customer_id}", json=customer_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Update customer failed", e)
            return None

    def delete_customer(self, customer_id, version):
        try:
            response = self.client.post(f"/customers/{customer_id}/deactivate", json={"expected_version": version})
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            self._handle_error("Delete customer failed", e)
            return False

    def get_sales(self):
        try:
            response = self.client.get("/sales")
            response.raise_for_status()
            return response.json()["items"]
        except httpx.HTTPError as e:
            self._handle_error("Fetch sales failed", e)
            return []

    def create_sale(self, sale_data):
        try:
            response = self.client.post("/sales", json=sale_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Create sale failed", e)
            return None

    def get_sale(self, sale_id):
        try:
            response = self.client.get(f"/sales/{sale_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Fetch sale failed", e)
            return None

    def create_return(self, return_data):
        try:
            response = self.client.post("/returns", json=return_data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Create return failed", e)
            return None

    def get_returns(self, limit=20):
        try:
            response = self.client.get("/returns", params={"limit": limit})
            response.raise_for_status()
            return response.json()["items"]
        except httpx.HTTPError as e:
            self._handle_error("Fetch returns failed", e)
            return []

    def get_employees(self, search=None, active=None, limit=20):
        try:
            params = {"limit": limit}
            if search: params["search"] = search
            if active is not None: params["active"] = str(active).lower()
            
            response = self.client.get("/employees", params=params)
            response.raise_for_status()
            return response.json()["items"]
        except httpx.HTTPError as e:
            self._handle_error("Fetch employees failed", e)
            return []

    def create_employee(self, data):
        try:
            response = self.client.post("/employees", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Create employee failed", e)
            return None

    def update_employee(self, employee_id, data):
        try:
            response = self.client.patch(f"/employees/{employee_id}", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Update employee failed", e)
            return None

    def grant_increment(self, employee_id, data):
        try:
            response = self.client.post(f"/employees/{employee_id}/increment", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Grant increment failed", e)
            return None

    def give_bonus(self, employee_id, data):
        try:
            response = self.client.post(f"/employees/{employee_id}/bonus", json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Give bonus failed", e)
            return None

    def get_financial_history(self, employee_id):
        try:
            response = self.client.get(f"/employees/{employee_id}/financial-history")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Fetch financial history failed", e)
            return None

    def get_users(self, search=None, role=None, active=None, limit=20):
        try:
            params = {"limit": limit}
            if search: params["search"] = search
            if role: params["role"] = role
            if active is not None: params["active"] = str(active).lower()
            
            response = self.client.get("/auth/users", params=params)
            response.raise_for_status()
            return response.json()["items"]
        except httpx.HTTPError as e:
            self._handle_error("Fetch users failed", e)
            return []

    def update_user_role(self, user_id, role, current_version):
        try:
            response = self.client.post(
                f"/auth/users/{user_id}/role", 
                json={"role": role, "expected_version": current_version}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Update user role failed", e)
            return None

    def deactivate_user(self, user_id, current_version):
        try:
            response = self.client.post(
                f"/auth/users/{user_id}/deactivate", 
                json={"expected_version": current_version}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Deactivate user failed", e)
            return None

    def activate_user(self, user_id, current_version):
        try:
            response = self.client.post(
                f"/auth/users/{user_id}/activate", 
                json={"expected_version": current_version}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Activate user failed", e)
            return None
            
    def reset_user_password(self, user_id, new_password, current_version):
        try:
            response = self.client.post(
                f"/auth/users/{user_id}/password", 
                json={"new_password": new_password, "expected_version": current_version}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self._handle_error("Reset password failed", e)
            return None

api_service = ApiService()
