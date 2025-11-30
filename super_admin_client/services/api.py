import httpx

class ApiClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.token = None

    def set_token(self, token):
        self.token = token

    def _get_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def login(self, username, password):
        try:
            res = httpx.post(f"{self.base_url}/auth/token", data={
                "username": username,
                "password": password
            })
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"Login error: {e}")
            return None

    def get_tenants(self):
        try:
            res = httpx.get(f"{self.base_url}/tenants/", headers=self._get_headers())
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"Get tenants error: {e}")
            return []

    def get_plans(self):
        try:
            res = httpx.get(f"{self.base_url}/tenants/plans", headers=self._get_headers())
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"Get plans error: {e}")
            return []

    def create_tenant(self, name, subscription_plan_id, domain=None):
        try:
            res = httpx.post(
                f"{self.base_url}/tenants/", 
                headers=self._get_headers(),
                params={
                    "name": name,
                    "subscription_plan_id": subscription_plan_id,
                    "domain": domain
                }
            )
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"Create tenant error: {e}")
            return None

api_client = ApiClient()
