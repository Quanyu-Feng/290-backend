import os
import json
import hmac
import hashlib
from http.server import BaseHTTPRequestHandler

# 从环境变量读取密钥（如果你在飞书开启了凭证校验）
FEISHU_VERIFY_TOKEN = os.environ.get("FEISHU_VERIFY_TOKEN", "")

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        """用于浏览器访问，确认端点存活"""
        self._json(200, {"status": "webhook endpoint alive"})

    def do_POST(self):
        # 1. 安全校验：如果配置了 VERIFY_TOKEN，则进行验证
        if FEISHU_VERIFY_TOKEN:
            auth_header = self.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                self._json(401, {"error": "Missing or invalid Authorization header"})
                return
            token = auth_header[7:]
            if token != FEISHU_VERIFY_TOKEN:
                self._json(401, {"error": "Invalid token"})
                return

        # 2. 读取请求体
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")

        # 3. 打印日志，用于调试
        print(f"[webhook] Received body: {raw}")

        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            self._json(400, {"error": "Invalid JSON"})
            return

        # 4. （可选）处理飞书 URL 验证请求
        if body.get("type") == "url_verification" or "challenge" in body:
            self._json(200, {"challenge": body.get("challenge", "")})
            return

        # 5. 在这里处理业务逻辑，比如解析 record_id，调用飞书 API 拉取完整记录，并同步到 Supabase
        # 目前先返回成功，确认链路
        record_id = body.get("record_id")
        print(f"[webhook] Processing record: {record_id}")

        self._json(200, {"code": 0, "msg": "received"})

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
