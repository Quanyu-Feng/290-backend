from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        """浏览器直接访问时，用来确认端点活着"""
        self._json(200, {"status": "webhook endpoint alive"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")

        # 这两行会出现在 Vercel 的 Logs 里，方便调试
        print(f"[webhook] headers: {dict(self.headers)}")
        print(f"[webhook] body: {raw}")

        try:
            body = json.loads(raw)
        except Exception:
            body = {"_raw": raw}

        # 飞书事件订阅的 URL 验证（如果以后用开放平台事件会用到）
        if body.get("type") == "url_verification" or "challenge" in body:
            self._json(200, {"challenge": body.get("challenge", "")})
            return

        # 其他内容一律收下，先原样返回，不做业务
        self._json(200, {"code": 0, "msg": "received"})

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
