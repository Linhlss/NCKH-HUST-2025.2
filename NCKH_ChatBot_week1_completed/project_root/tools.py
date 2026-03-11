from __future__ import annotations

import ast
from typing import Any, Dict, Optional

from config import load_tenant_configs
from ingestion import (
    list_real_files,
    read_links,
    selected_shared_files_dir,
    selected_shared_links_file,
    tenant_files_dir,
    tenant_links_file,
)
from memory_store import MemoryStore
from models import TenantProfile
from runtime_manager import RUNTIME_CACHE, build_runtime
from utils import HAS_PSUTIL, HAS_SCHEDULER, format_ram_usage, get_ram_usage, now_str


_ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
}
_ALLOWED_UNARYOPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}


def _eval_ast(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](_eval_ast(node.left), _eval_ast(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_eval_ast(node.operand))
    raise ValueError("Biểu thức không được hỗ trợ")


def safe_calculate(expr: str) -> str:
    try:
        parsed = ast.parse(expr, mode="eval")
        value = _eval_ast(parsed)
        return str(value)
    except Exception as exc:
        return f"Lỗi: {exc}"


def tool_current_time() -> str:
    return f"Thời gian hiện tại: {now_str()}"


def tool_list_docs(profile: TenantProfile) -> str:
    shared_dir = selected_shared_files_dir()
    tenant_dir = tenant_files_dir(profile.tenant_id)
    shared_docs = [p.name for p in list_real_files(shared_dir)] if shared_dir else []
    tenant_docs = [p.name for p in list_real_files(tenant_dir)]
    shared_links = read_links(selected_shared_links_file())
    tenant_links = read_links(tenant_links_file(profile.tenant_id))

    return (
        f"--- DANH SÁCH DỮ LIỆU ---\n"
        f"Shared files: {shared_docs or '[]'}\n"
        f"Tenant files: {tenant_docs or '[]'}\n"
        f"Shared links: {shared_links or '[]'}\n"
        f"Tenant links: {tenant_links or '[]'}"
    )


def tool_list_tenants() -> str:
    configs = load_tenant_configs()
    return f"Danh sách tenant: {list(configs.keys())}"


def tool_status(profile: TenantProfile, user_id: str) -> str:
    rt = RUNTIME_CACHE.get(profile.tenant_id)
    ram = format_ram_usage(get_ram_usage())
    return (
        f"--- STATUS ---\n"
        f"Tenant: {profile.tenant_id}\n"
        f"User: {user_id}\n"
        f"RAM: {ram}\n"
        f"Docs: {rt.document_count if rt else 'N/A'}\n"
        f"Nodes: {rt.node_count if rt else 'N/A'}\n"
        f"Loaded at: {rt.loaded_at if rt else 'N/A'}\n"
        f"Model: {profile.model_name}\n"
        f"Scheduler: {'enabled' if HAS_SCHEDULER else 'unavailable'}\n"
        f"psutil: {'enabled' if HAS_PSUTIL else 'unavailable'}"
    )


def tool_refresh(profile: TenantProfile) -> str:
    rt = build_runtime(profile, force_rebuild=True)
    return f"Đã làm mới dữ liệu lúc {rt.loaded_at}."


def detect_direct_tool(question: str, profile: TenantProfile, user_id: str) -> Optional[str]:
    q = question.strip().lower()

    if q in {"time", "giờ", "mấy giờ rồi", "thời gian hiện tại", "current time"}:
        return tool_current_time()
    if q in {"status", "trạng thái", "system status"}:
        return tool_status(profile, user_id)
    if q in {"listdocs", "list docs", "danh sách tài liệu", "liệt kê tài liệu"}:
        return tool_list_docs(profile)
    if q in {"tenants", "list tenants", "danh sách tenant"}:
        return tool_list_tenants()
    if q.startswith("calc "):
        return f"Kết quả tính toán: {safe_calculate(question[5:])}"
    if q.startswith("tính "):
        return f"Kết quả tính toán: {safe_calculate(question[5:])}"

    return None


def handle_slash_command(
    cmd_raw: str,
    profile: TenantProfile,
    user_id: str,
    state: Dict[str, Any],
):
    q = cmd_raw.strip()
    q_lower = q.lower()

    if q_lower == "/help":
        msg = (
            "Lệnh hỗ trợ:\n"
            "/status\n"
            "/tenants\n"
            "/listdocs\n"
            "/refresh hoặc /reindex\n"
            "/resetmem\n"
            "/switch <tenant> <user>\n"
            "/time\n"
            "/calc <biểu_thức>\n"
            "/sources on | /sources off"
        )
        return profile, user_id, msg

    if q_lower == "/status":
        return profile, user_id, tool_status(profile, user_id)

    if q_lower == "/tenants":
        return profile, user_id, tool_list_tenants()

    if q_lower == "/listdocs":
        return profile, user_id, tool_list_docs(profile)

    if q_lower in {"/refresh", "/reindex"}:
        return profile, user_id, tool_refresh(profile)

    if q_lower == "/resetmem":
        MemoryStore(profile.tenant_id, user_id).reset()
        return profile, user_id, "Đã xóa sạch bộ nhớ hội thoại."

    if q_lower == "/time":
        return profile, user_id, tool_current_time()

    if q_lower.startswith("/calc "):
        return profile, user_id, f"Kết quả tính toán: {safe_calculate(q[6:])}"

    if q_lower.startswith("/switch "):
        parts = q.split()
        new_tenant = parts[1] if len(parts) > 1 else "default"
        new_user = parts[2] if len(parts) > 2 else user_id
        state["tenant_id"] = new_tenant
        state["user_id"] = new_user
        from llm_service import get_or_create_profile
        new_profile = get_or_create_profile(new_tenant)
        return new_profile, new_user, f"Đã chuyển sang Tenant: {new_tenant}, User: {new_user}"

    if q_lower == "/sources on":
        state["show_sources"] = True
        return profile, user_id, "Đã bật hiển thị nguồn."

    if q_lower == "/sources off":
        state["show_sources"] = False
        return profile, user_id, "Đã tắt hiển thị nguồn."

    return profile, user_id, "Lệnh không hợp lệ. Gõ /help để xem danh sách."