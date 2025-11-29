import httpx
import sys

API_URL = "http://localhost:8000/api/v1"
EMAIL = "admin@retailpos.com"
PASSWORD = "AdminPass123!"

def add_stock():
    # 1. Login
    print("Logging in...")
    resp = httpx.post(f"{API_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Products
    print("Fetching products...")
    resp = httpx.get(f"{API_URL}/products", headers=headers)
    if resp.status_code != 200:
        print(f"Get products failed: {resp.text}")
        return
    products = resp.json()["items"]
    
    if not products:
        print("No products found.")
        return

    # 3. Add Stock
    for product in products:
        print(f"Adding stock for {product['name']} (ID: {product['id']})...")
        movement_data = {
            "quantity": 100,
            "direction": "in",
            "reason": "Initial Stock",
            "reference": "SETUP-001"
        }
        resp = httpx.post(
            f"{API_URL}/products/{product['id']}/inventory/movements",
            json=movement_data,
            headers=headers
        )
        if resp.status_code == 201:
            print(f"SUCCESS: Added 100 units to {product['name']}")
        else:
            print(f"FAILURE: Failed to add stock to {product['name']}: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    add_stock()
