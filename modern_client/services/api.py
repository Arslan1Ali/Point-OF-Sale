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

    def get_products(self, search=None, category_id=None, active=None):
        try:
            params = {}
            if search: params["search"] = search
            if category_id: params["category_id"] = category_id
            if active is not None: params["active"] = str(active).lower()
            
            response = self.client.get("/products", params=params)
            response.raise_for_status()
            return response.json()["items"]
        except httpx.HTTPError as e:
            self._handle_error("Fetch products failed", e)
            return []

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
        try:
            # Backend requires expected_version for deactivation/deletion
            response = self.client.delete(f"/products/{product_id}", json={"expected_version": version})
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            self._handle_error("Delete product failed", e)
            return False

    def get_customers(self):
        try:
            response = self.client.get("/customers")
            response.raise_for_status()
            return response.json()["items"]
        except httpx.HTTPError as e:
            self._handle_error("Fetch customers failed", e)
            return []

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

api_service = ApiService()
