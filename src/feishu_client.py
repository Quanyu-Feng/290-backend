import requests
import time
from typing import Dict, List, Any

BASE_URL = "https://open.feishu.cn/open-apis"

class FeishuClient:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token = None
        self._token_expire_at = 0

    def _refresh_token(self):
        """tenant_access_token 自动刷新"""
        if self._token and time.time() < self._token_expire_at - 60:
            return
        resp = requests.post(
            f"{BASE_URL}/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
        )
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"获取 token 失败: {data}")
        self._token = data["tenant_access_token"]
        self._token_expire_at = time.time() + data.get("expire", 7200)

    def _headers(self) -> Dict[str, str]:
        self._refresh_token()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def fetch_all_records(self, app_token: str, table_id: str) -> List[Dict]:
        """分页拉取全量记录"""
        url = f"{BASE_URL}/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        records = []
        page_token = None
        while True:
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token
            resp = requests.get(url, headers=self._headers(), params=params)
            data = resp.json().get("data", {})
            records.extend(data.get("items", []))
            if not data.get("has_more"):
                break
            page_token = data.get("page_token")
        return records
