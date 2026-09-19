import os
from http.server import BaseHTTPRequestHandler
import json

from src.feishu_client import FeishuClient
from src.transformer import transform_record
from src.supabase_client import SupabaseWriter

# 环境变量
APP_ID = os.environ["FEISHU_APP_ID"]
APP_SECRET = os.environ["FEISHU_APP_SECRET"]
APP_TOKEN = os.environ["FEISHU_APP_TOKEN"]
SOURCE_TABLE_ID = os.environ["FEISHU_SOURCE_TABLE_ID"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TARGET_TABLE = "project_initiation"


def run_sync():
    """执行一次全量同步（UPSERT 模式）"""
    feishu = FeishuClient(APP_ID, APP_SECRET)
    supabase = SupabaseWriter(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # 1. 拉取飞书全量记录
    raw_records = feishu.fetch_all_records(APP_TOKEN, SOURCE_TABLE_ID)
    print(f"[同步] 飞书返回 {len(raw_records)} 条记录")

    # 2. 转换为 PostgreSQL 行数据
    rows = [transform_record(r) for r in raw_records]

    # 3. UPSERT 到 Supabase
    written = supabase.upsert_records(TARGET_TABLE, rows)
    print(f"[同步] 写入 {written} 条记录")

    return {"status": "ok", "total": len(raw_records), "written": written}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Vercel Cron Job 触发入口"""
        try:
            result = run_sync()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
