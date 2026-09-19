import datetime
from typing import Any, Dict, List

# 字段名 → PostgreSQL 列名（你的 xlsx 中字段名与列名基本一致）
FIELD_MAP = {
    "申请编号": "申请编号",
    "项目立项编号": "项目立项编号",
    "申请状态": "申请状态",
    "审批流程": "审批流程",
    "发起时间": "发起时间",
    "完成时间": "完成时间",
    "发起人": "发起人",
    "发起人部门": "发起人部门",
    "当前处理人": "当前处理人",
    "项目负责人": "项目负责人",
    "项目负责人部门": "项目负责人部门",
    "项目负责人职位": "项目负责人职位",
    "项目负责人1": "项目负责人1",
    "项目负责人部门1": "项目负责人部门1",
    "项目负责人职位1": "项目负责人职位1",
    "项目类型": "项目类型",
    "业务": "业务",
    "项目涉及部门": "项目涉及部门",
    "项目名称": "项目名称",
    "项目成员": "项目成员",
    "客户名称": "客户名称",
    "客户背景": "客户背景",
    "项目说明": "项目说明",
    "风险自评": "风险自评",
    "执行委员会决议": "执行委员会决议",
    "预计收入": "预计收入",
    "预计收入-币种": "预计收入币种",
    "预计月收入": "预计月收入",
    "预计月收入-币种": "预计月收入币种",
    "渠道费": "渠道费",
    "使用集团资金": "使用集团资金",
    "需要企业传讯部宣发": "需要企业传讯部宣发",
    "其他信息": "其他信息",
    "项目管理文档链接": "项目管理文档链接",
    "提交人": "提交人",
    "提交人部门": "提交人部门",
    "提交人职位": "提交人职位",
    "项目负责人2": "项目负责人2",
    "项目负责人所在部门": "项目负责人所在部门",
    "项目负责人职位2": "项目负责人职位2",
    "立项流水号": "立项流水号",
    "项目编号": "项目编号",
    "业务归属部门": "业务归属部门",
    "业务类型": "业务类型",
    "SourceID": "source_id",
    "最后更新时间": "最后更新时间",
}

# 字段类型分类（对应你的 xlsx 中的数据）
FIELD_TYPES = {
    "申请编号": "hyperlink",
    "项目立项编号": "text",
    "申请状态": "text",
    "审批流程": "text",
    "发起时间": "date",
    "完成时间": "date",
    "发起人": "person",
    "发起人部门": "text",
    "当前处理人": "person",
    "项目负责人": "person",
    "项目负责人部门": "text",
    "项目负责人职位": "text",
    "项目负责人1": "person",
    "项目负责人部门1": "text",
    "项目负责人职位1": "text",
    "项目类型": "text",
    "业务": "text",
    "项目涉及部门": "multi_select",
    "项目名称": "text",
    "项目成员": "person",
    "客户名称": "text",
    "客户背景": "text",
    "项目说明": "text",
    "风险自评": "text",
    "执行委员会决议": "hyperlink",
    "预计收入": "number",
    "预计收入-币种": "text",
    "预计月收入": "number",
    "预计月收入-币种": "text",
    "渠道费": "text",
    "使用集团资金": "text",
    "需要企业传讯部宣发": "text",
    "其他信息": "text",
    "项目管理文档链接": "hyperlink",
    "提交人": "person",
    "提交人部门": "text",
    "提交人职位": "text",
    "项目负责人2": "person",
    "项目负责人所在部门": "text",
    "项目负责人职位2": "text",
    "立项流水号": "text",
    "项目编号": "text",
    "业务归属部门": "text",
    "业务类型": "text",
    "SourceID": "text",
    "最后更新时间": "date",
}


def _extract_text(value: Any) -> str | None:
    """从飞书文本/超链接结构中提取纯文本"""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list) and value:
        item = value[0]
        if isinstance(item, dict):
            return (item.get("text") or item.get("name") or "").strip() or None
        return str(item).strip() or None
    if isinstance(value, dict):
        return (value.get("text") or value.get("name") or "").strip() or None
    return str(value).strip() or None


def _extract_person(value: Any) -> List[Dict]:
    """提取人员列表，返回 [{"id": "ou_xxx", "name": "xxx"}]"""
    result = []
    items = value if isinstance(value, list) else [value] if value else []
    for item in items:
        if isinstance(item, dict):
            uid = item.get("id")
            name = item.get("name") or item.get("en_name")
            if uid:
                result.append({"id": uid, "name": name or ""})
    return result


def _extract_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip().replace(",", "")
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    if isinstance(value, list) and value:
        return _extract_number(value[0])
    if isinstance(value, dict):
        return _extract_number(value.get("value") or value.get("text"))
    return None


def _extract_date(value: Any) -> str | None:
    """将飞书毫秒时间戳转为 ISO 格式字符串，PostgreSQL 可直接解析"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = int(value)
        if ts > 1e12:  # 毫秒
            ts = ts / 1000
        return datetime.datetime.fromtimestamp(ts).isoformat()
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        # 尝试常见格式
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                     "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
            try:
                return datetime.datetime.strptime(s, fmt).isoformat()
            except ValueError:
                continue
        return s  # 可能已经是 ISO 格式
    if isinstance(value, list) and value:
        return _extract_date(value[0])
    return None


def _extract_multi_select(value: Any) -> List[str]:
    """提取多选值"""
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, dict):
                t = item.get("text") or item.get("name")
                if t:
                    result.append(t)
            elif isinstance(item, str) and item.strip():
                result.append(item.strip())
        return result
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _extract_hyperlink(value: Any) -> Dict | None:
    """提取超链接，返回 {"text": "...", "link": "..."}"""
    if value is None:
        return None
    if isinstance(value, list) and value:
        item = value[0]
        if isinstance(item, dict):
            text = item.get("text", "")
            link = item.get("link", "")
            if text or link:
                return {"text": text, "link": link}
        return None
    if isinstance(value, dict):
        return {"text": value.get("text", ""), "link": value.get("link", "")}
    s = str(value).strip()
    if s:
        return {"text": s, "link": ""}
    return None


def transform_record(feishu_record: Dict) -> Dict:
    """
    将飞书记录转换为 PostgreSQL 行数据
    返回可直接用于 UPSERT 的 dict
    """
    fields = feishu_record.get("fields", {})
    row = {"record_id": feishu_record["record_id"]}

    for src_name, col_name in FIELD_MAP.items():
        raw = fields.get(src_name)
        ftype = FIELD_TYPES.get(src_name, "text")

        if ftype == "text":
            row[col_name] = _extract_text(raw)
        elif ftype == "number":
            row[col_name] = _extract_number(raw)
        elif ftype == "date":
            row[col_name] = _extract_date(raw)
        elif ftype == "person":
            row[col_name] = _extract_person(raw)
        elif ftype == "multi_select":
            row[col_name] = _extract_multi_select(raw)
        elif ftype == "hyperlink":
            row[col_name] = _extract_hyperlink(raw)
        else:
            row[col_name] = _extract_text(raw)

    return row