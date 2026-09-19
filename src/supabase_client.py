from supabase import create_client, Client

class SupabaseWriter:
    def __init__(self, url: str, service_key: str):
        self.client: Client = create_client(url, service_key)

    def upsert_records(self, table: str, rows: list[dict], batch_size: int = 500):
        """按 record_id 批量 UPSERT"""
        total = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            resp = (
                self.client.table(table)
                .upsert(batch, on_conflict="record_id")
                .execute()
            )
            total += len(batch)
        return total

    def get_latest_updated_at(self, table: str) -> str | None:
        """获取数据库中最大的最后更新时间，用于增量判断"""
        resp = (
            self.client.table(table)
            .select("最后更新时间")
            .order("最后更新时间", desc=True)
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0].get("最后更新时间")
        return None