from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib import error, parse, request

import streamlit as st

from evaluation.generate_test_queries import build_source_items, save_generated_queries
from project_root.ingestion import tenant_files_dir, tenant_links_file


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config" / "tenants.json"
DATA_FILES_DIR = BASE_DIR / "data" / "files"
PIPELINE1_DIR = BASE_DIR / "pipeline1"
GENERATED_QA_PATH = PIPELINE1_DIR / "generated_qa.json"
LORA_DATASET_PATH = PIPELINE1_DIR / "lora_dataset.json"
EVAL_DATASET_PATH = BASE_DIR / "evaluation" / "test_queries.json"
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
FILE_TOKEN_RE = re.compile(r"(\/[^\s'\"<>]+\.(?:pdf|docx|doc|xlsx|xls|csv|txt|md))", re.IGNORECASE)


def http_json(method: str, url: str, payload: Dict[str, Any] | None = None, timeout: int = 120) -> Dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url=url, method=method.upper(), data=data, headers=headers)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else {}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"message": body or str(exc)}
        raise RuntimeError(f"{exc.code} {exc.reason}: {parsed}")
    except error.URLError as exc:
        raise RuntimeError(f"Không kết nối được API: {exc}")


def api_connection_status(api_base: str) -> Tuple[bool, str]:
    try:
        payload = http_json("GET", f"{api_base.rstrip('/')}/health", timeout=2)
        return True, payload.get("status", "ok")
    except Exception as exc:
        return False, str(exc)


def load_tenant_configs() -> Dict[str, Dict[str, Any]]:
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def save_tenant_configs(configs: Dict[str, Dict[str, Any]]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(configs, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_tenant_id(raw: str) -> str:
    normalized = re.sub(r"[^a-z0-9_]+", "_", raw.lower()).strip("_")
    return normalized or "tenant_moi"


def run_pipeline1() -> Tuple[int, str]:
    cmd = [sys.executable, str(PIPELINE1_DIR / "run_pipeline1.py")]
    proc = subprocess.run(
        cmd,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, output.strip()


def count_json_records(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    return len(data) if isinstance(data, list) else 0


def ensure_data_dir() -> None:
    DATA_FILES_DIR.mkdir(parents=True, exist_ok=True)


def append_unique_links(path: Path, links: List[str]) -> List[str]:
    existing = []
    if path.exists():
        existing = [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
    merged = list(existing)
    added: List[str] = []
    for link in links:
        if link not in merged:
            merged.append(link)
            added.append(link)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(merged) + ("\n" if merged else ""), encoding="utf-8")
    return added


def persist_tenant_links(tenant_id: str, links: List[str]) -> List[str]:
    if not links:
        return []
    return append_unique_links(tenant_links_file(tenant_id), links)


def persist_tenant_files(tenant_id: str, uploaded_files: List[Any]) -> List[str]:
    saved: List[str] = []
    target_dir = tenant_files_dir(tenant_id)
    for item in uploaded_files:
        target = target_dir / item.name
        target.write_bytes(item.getbuffer())
        saved.append(str(target))
    return saved


def persist_file_paths_from_prompt(tenant_id: str, prompt: str) -> List[str]:
    target_dir = tenant_files_dir(tenant_id)
    saved: List[str] = []
    matches = FILE_TOKEN_RE.findall(prompt or "")
    for raw in matches:
        source = Path(raw).expanduser()
        if not source.exists() or not source.is_file():
            continue
        target = target_dir / source.name
        if source.resolve() == target.resolve():
            saved.append(str(target))
            continue
        target.write_bytes(source.read_bytes())
        saved.append(str(target))
    return saved


def refresh_tenant_runtime(api_base: str, tenant_id: str) -> Tuple[bool, str]:
    try:
        payload = http_json("POST", f"{api_base.rstrip('/')}/refresh", {"tenant_id": tenant_id})
        return True, payload.get("message", "Đã refresh dữ liệu.")
    except Exception as exc:
        return False, str(exc)


def regenerate_queries_for_sources(tenant_id: str, file_paths: List[str], links: List[str]) -> Tuple[bool, str]:
    try:
        sources = build_source_items(file_paths, links, tenant_id)
        count = save_generated_queries(sources, output=EVAL_DATASET_PATH, merge_existing=True)
        return True, f"Đã cập nhật evaluation/test_queries.json ({count} records sau khi merge)."
    except Exception as exc:
        return False, f"Không regenerate được queries: {exc}"


def extract_links_from_prompt(prompt: str) -> List[str]:
    cleaned = []
    for match in URL_RE.findall(prompt or ""):
        link = match.rstrip(").,;]}>")
        if link not in cleaned:
            cleaned.append(link)
    return cleaned


def ingest_chat_sources(
    tenant_id: str,
    api_base: str,
    prompt: str = "",
    uploaded_files: List[Any] | None = None,
    manual_links: List[str] | None = None,
) -> Dict[str, Any]:
    uploaded_files = uploaded_files or []
    manual_links = manual_links or []
    prompt_links = extract_links_from_prompt(prompt)
    all_links = list(dict.fromkeys([*manual_links, *prompt_links]))

    saved_files = persist_tenant_files(tenant_id, uploaded_files)
    saved_files.extend([path for path in persist_file_paths_from_prompt(tenant_id, prompt) if path not in saved_files])
    added_links = persist_tenant_links(tenant_id, all_links)

    changed = bool(saved_files or added_links)
    refresh_ok, refresh_note = (True, "Không cần refresh.") if not changed else refresh_tenant_runtime(api_base, tenant_id)
    regen_ok, regen_note = (True, "Không cần regenerate queries.") if not changed else regenerate_queries_for_sources(tenant_id, saved_files, added_links)

    return {
        "changed": changed,
        "saved_files": saved_files,
        "added_links": added_links,
        "refresh_ok": refresh_ok,
        "refresh_note": refresh_note,
        "regen_ok": regen_ok,
        "regen_note": regen_note,
    }


def session_chat_key(tenant_id: str, user_id: str) -> str:
    user = user_id.strip() or "guest"
    return f"{tenant_id}::{user}"


def get_chat_store() -> Dict[str, List[Dict[str, Any]]]:
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {}
    return st.session_state.chat_sessions


def get_messages(chat_key: str) -> List[Dict[str, Any]]:
    return get_chat_store().setdefault(chat_key, [])


def append_message(chat_key: str, role: str, content: str, meta: Dict[str, Any] | None = None) -> None:
    get_messages(chat_key).append(
        {
            "role": role,
            "content": content,
            "meta": meta or {},
        }
    )


def clear_messages(chat_key: str) -> None:
    get_chat_store()[chat_key] = []


def nl2br(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def render_message(role: str, content: str, meta: Dict[str, Any] | None = None) -> None:
    meta = meta or {}
    side_class = "user-row" if role == "user" else "assistant-row"
    bubble_class = "user-bubble" if role == "user" else "assistant-bubble"
    label = "Bạn" if role == "user" else "Trợ lý"

    pills: List[str] = []
    for key in ["route", "mode", "latency_ms"]:
        value = meta.get(key)
        if value is None or value == "":
            continue
        if key == "latency_ms":
            pills.append(f"{value} ms")
        else:
            pills.append(str(value))

    pills_html = "".join(f"<span class='msg-pill'>{html.escape(pill)}</span>" for pill in pills)

    st.markdown(
        f"""
        <div class="chat-row {side_class}">
            <div class="chat-bubble {bubble_class}">
                <div class="chat-label">{label}</div>
                <div class="chat-content">{nl2br(content)}</div>
                {"<div class='chat-meta'>" + pills_html + "</div>" if pills_html else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sources = meta.get("sources") or []
    if role == "assistant" and sources:
        with st.expander("Nguồn tham khảo", expanded=False):
            st.dataframe(sources, use_container_width=True)

    metadata = meta.get("metadata") or {}
    if role == "assistant" and metadata:
        with st.expander("Chi tiết phản hồi", expanded=False):
            st.json(metadata)


st.set_page_config(page_title="Multi-tenant RAG Control Panel", page_icon=":robot_face:", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --bg-main: #f3f5ef;
        --bg-panel: rgba(255,255,255,0.78);
        --bg-panel-strong: rgba(255,255,255,0.95);
        --line: #d7ddd2;
        --text-main: #1f2a1f;
        --text-soft: #5e6c5c;
        --accent: #1f7a63;
        --accent-strong: #115746;
        --assistant: #ffffff;
        --user: linear-gradient(135deg, #1f7a63 0%, #145144 100%);
        --shadow: 0 18px 50px rgba(31, 54, 43, 0.08);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(31,122,99,0.14), transparent 26%),
            radial-gradient(circle at top right, rgba(210,180,140,0.18), transparent 22%),
            linear-gradient(180deg, #eef2ea 0%, #f7f8f4 100%);
        color: var(--text-main);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8eee8 0%, #eef2ef 100%);
        border-right: 1px solid rgba(31, 54, 43, 0.08);
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(247,249,245,0.82));
        border: 1px solid rgba(31, 54, 43, 0.08);
        box-shadow: var(--shadow);
        border-radius: 24px;
        padding: 28px 30px 20px;
        margin-bottom: 18px;
    }

    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        line-height: 1;
        color: #263126;
        margin-bottom: 10px;
        letter-spacing: -0.04em;
    }

    .hero-subtitle {
        font-size: 1rem;
        color: var(--text-soft);
        max-width: 920px;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border-radius: 999px;
        padding: 8px 14px;
        font-size: 0.92rem;
        font-weight: 600;
        margin-top: 16px;
        background: rgba(17, 87, 70, 0.08);
        color: var(--accent-strong);
        border: 1px solid rgba(17, 87, 70, 0.12);
    }

    .status-pill.offline {
        background: rgba(163, 52, 48, 0.08);
        color: #9f2f2a;
        border-color: rgba(163, 52, 48, 0.14);
    }

    .chat-shell {
        background: rgba(255,255,255,0.7);
        border: 1px solid rgba(31, 54, 43, 0.08);
        box-shadow: var(--shadow);
        border-radius: 24px;
        padding: 20px 18px 12px;
        backdrop-filter: blur(10px);
    }

    .chat-row {
        display: flex;
        width: 100%;
        margin: 0.4rem 0 0.9rem;
    }

    .assistant-row {
        justify-content: flex-start;
    }

    .user-row {
        justify-content: flex-end;
    }

    .chat-bubble {
        max-width: 78%;
        border-radius: 22px;
        padding: 14px 16px 12px;
        box-shadow: 0 12px 28px rgba(31, 54, 43, 0.09);
        border: 1px solid rgba(31, 54, 43, 0.08);
    }

    .assistant-bubble {
        background: var(--assistant);
        color: var(--text-main);
        border-top-left-radius: 8px;
    }

    .user-bubble {
        background: var(--user);
        color: #ffffff;
        border-top-right-radius: 8px;
        border: none;
    }

    .chat-label {
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        opacity: 0.78;
        margin-bottom: 0.45rem;
    }

    .chat-content {
        font-size: 1rem;
        line-height: 1.7;
        word-break: break-word;
    }

    .chat-meta {
        margin-top: 0.8rem;
    }

    .msg-pill {
        display: inline-block;
        padding: 5px 10px;
        margin-right: 6px;
        margin-bottom: 6px;
        border-radius: 999px;
        background: rgba(20, 30, 20, 0.06);
        font-size: 0.78rem;
        font-weight: 600;
    }

    .empty-chat {
        padding: 32px 20px;
        text-align: center;
        color: var(--text-soft);
        border: 1px dashed rgba(31, 54, 43, 0.14);
        border-radius: 18px;
        background: rgba(255,255,255,0.55);
        margin-bottom: 10px;
    }

    .chat-tip-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-top: 12px;
    }

    .chat-tip {
        background: rgba(255,255,255,0.8);
        border: 1px solid rgba(31, 54, 43, 0.08);
        border-radius: 16px;
        padding: 14px;
        color: var(--text-main);
        font-size: 0.92rem;
    }

    div[data-testid="stChatInput"] {
        background: rgba(255,255,255,0.86);
        border: 1px solid rgba(31, 54, 43, 0.08);
        border-radius: 18px;
        box-shadow: var(--shadow);
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.82);
        border: 1px solid rgba(31, 54, 43, 0.08);
        border-radius: 18px;
        padding: 8px 10px;
    }

    @media (max-width: 900px) {
        .hero-title {
            font-size: 2.2rem;
        }
        .chat-bubble {
            max-width: 92%;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

tenant_configs = load_tenant_configs()
tenant_options = sorted(tenant_configs.keys()) or ["default"]

with st.sidebar:
    st.subheader("Kết nối hệ thống")
    api_base = st.text_input("API base URL", value="http://127.0.0.1:8000")
    api_ok, api_note = api_connection_status(api_base)
    if api_ok:
        st.success("API đang hoạt động")
    else:
        st.error("API chưa kết nối được")
        st.caption(api_note)

    st.divider()
    st.subheader("Phiên làm việc")
    selected_tenant = st.selectbox("Tenant", tenant_options, index=0)
    user_id = st.text_input("User ID", value="guest")
    show_sources = st.checkbox("Hiện nguồn", value=True)

    active_chat_key = session_chat_key(selected_tenant, user_id)
    if st.button("Xóa lịch sử chat giao diện", use_container_width=True):
        clear_messages(active_chat_key)
        st.rerun()

st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-title">Multi-tenant RAG Control Panel</div>
        <div class="hero-subtitle">
            Bản giao diện phục vụ demo NCKH theo hướng hội thoại hiện đại hơn:
            chat liên tục, theo dõi tenant, kiểm tra runtime và chuẩn bị dữ liệu LoRA trong cùng một nơi.
        </div>
        <div class="status-pill {'offline' if not api_ok else ''}">
            {'API đã kết nối' if api_ok else 'API chưa sẵn sàng'} • Tenant hiện tại: {html.escape(selected_tenant)}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_chat, tab_runtime, tab_tenants, tab_lora = st.tabs(
    ["Chat", "Trạng thái hệ thống", "Cấu hình tenant", "Không gian LoRA"]
)

with tab_chat:
    chat_key = session_chat_key(selected_tenant, user_id)
    messages = get_messages(chat_key)
    if "chat_uploads" not in st.session_state:
        st.session_state.chat_uploads = {}
    if "chat_link_drafts" not in st.session_state:
        st.session_state.chat_link_drafts = {}
    upload_state_key = f"chat_upload::{selected_tenant}"
    link_state_key = f"chat_links::{selected_tenant}"

    top_col, side_col = st.columns([3.2, 1.2], gap="large")

    with top_col:
        st.subheader("Trò chuyện")
        st.caption("Tin nhắn của bạn nằm bên phải, phản hồi của trợ lý nằm bên trái ngay sau đó.")

        if messages:
            for message in messages:
                render_message(message["role"], message["content"], message.get("meta"))
        else:
            st.markdown(
                """
                <div class="empty-chat">
                    Chưa có hội thoại nào trong phiên này.<br>
                    Hãy bắt đầu bằng một câu hỏi về tài liệu, Excel, PDF hoặc thông tin nội bộ của tenant.
                </div>
                """,
                unsafe_allow_html=True,
            )

    with side_col:
        st.subheader("Gợi ý hỏi nhanh")
        st.markdown(
            """
            <div class="chat-tip-grid">
                <div class="chat-tip">File Excel của tôi đang chứa những gì?</div>
                <div class="chat-tip">Liệt kê các học phần trong dữ liệu hiện có.</div>
                <div class="chat-tip">Kiểm tra trạng thái runtime của tenant này.</div>
                <div class="chat-tip">Tài liệu PDF nào đang được dùng để trả lời?</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        st.subheader("Tổng quan phiên")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Số lượt chat", len(messages))
        with col_b:
            st.metric("Tenant", selected_tenant)
        st.metric("Người dùng", user_id.strip() or "guest")

        st.divider()
        st.subheader("Nguồn cho tenant")
        st.caption("Link trong prompt sẽ tự lưu. File mới có thể đính kèm ở đây để dùng ngay như dữ liệu trong data/.")

        chat_link_draft = st.text_area(
            "Link cần thêm vào tenant hiện tại",
            key=link_state_key,
            placeholder="Mỗi dòng một URL",
            height=90,
        )
        chat_uploads = st.file_uploader(
            "Đính kèm file cho tenant hiện tại",
            type=["pdf", "docx", "doc", "xlsx", "xls", "csv", "txt", "md"],
            accept_multiple_files=True,
            key=upload_state_key,
        )
        if st.button("Lưu nguồn vào tenant + refresh", use_container_width=True):
            manual_links = [line.strip() for line in (chat_link_draft or "").splitlines() if line.strip()]
            ingest_result = ingest_chat_sources(
                selected_tenant,
                api_base,
                prompt="",
                uploaded_files=list(chat_uploads or []),
                manual_links=manual_links,
            )
            if ingest_result["changed"]:
                st.success(
                    f"Đã lưu {len(ingest_result['saved_files'])} file và {len(ingest_result['added_links'])} link. "
                    f"{ingest_result['refresh_note']} {ingest_result['regen_note']}"
                )
            else:
                st.info("Không có file/link mới để lưu.")

    prompt = st.chat_input("Nhập câu hỏi của bạn...")
    if prompt:
        ingest_result = ingest_chat_sources(
            selected_tenant,
            api_base,
            prompt=prompt,
            uploaded_files=[],
            manual_links=[],
        )
        append_message(chat_key, "user", prompt)
        payload = {
            "tenant_id": selected_tenant,
            "user_id": user_id.strip() or "guest",
            "message": prompt.strip(),
            "show_sources": show_sources,
        }

        try:
            with st.spinner("Đang lấy câu trả lời từ hệ thống..."):
                resp = http_json("POST", f"{api_base.rstrip('/')}/chat", payload)
            append_message(
                chat_key,
                "assistant",
                resp.get("answer", ""),
                {
                    "route": resp.get("route", "unknown"),
                    "mode": resp.get("mode", "unknown"),
                    "latency_ms": (resp.get("metadata") or {}).get("latency_ms"),
                    "sources": resp.get("sources") or [],
                    "metadata": {
                        **(resp.get("metadata") or {}),
                        "auto_ingest": {
                            "saved_files": ingest_result["saved_files"],
                            "added_links": ingest_result["added_links"],
                            "refresh_ok": ingest_result["refresh_ok"],
                            "refresh_note": ingest_result["refresh_note"],
                            "regen_ok": ingest_result["regen_ok"],
                            "regen_note": ingest_result["regen_note"],
                        },
                    },
                },
            )
        except Exception as exc:
            append_message(
                chat_key,
                "assistant",
                f"Lỗi hệ thống: {exc}",
                {"route": "error", "mode": "error"},
            )
        st.rerun()

with tab_runtime:
    st.subheader("Trạng thái runtime")
    st.caption("Dùng tab này để kiểm tra sức khỏe API, tình trạng tenant hiện tại và tác vụ refresh dữ liệu.")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Kiểm tra /health", use_container_width=True):
            try:
                st.json(http_json("GET", f"{api_base.rstrip('/')}/health"))
            except Exception as exc:
                st.error(str(exc))

    with col2:
        if st.button("Xem /status", use_container_width=True):
            query = parse.urlencode({"tenant_id": selected_tenant, "user_id": user_id.strip() or "guest"})
            try:
                st.json(http_json("GET", f"{api_base.rstrip('/')}/status?{query}"))
            except Exception as exc:
                st.error(str(exc))

    with col3:
        if st.button("Refresh Index Tenant", use_container_width=True):
            try:
                st.json(
                    http_json(
                        "POST",
                        f"{api_base.rstrip('/')}/refresh",
                        {"tenant_id": selected_tenant},
                    )
                )
            except Exception as exc:
                st.error(str(exc))

    if st.button("Reset Chat Memory", use_container_width=True):
        try:
            st.json(
                http_json(
                    "POST",
                    f"{api_base.rstrip('/')}/memory/reset",
                    {"tenant_id": selected_tenant, "user_id": user_id.strip() or "guest"},
                )
            )
        except Exception as exc:
            st.error(str(exc))

with tab_tenants:
    st.subheader("Cấu hình tenant")
    tenant_configs = load_tenant_configs()

    if not tenant_configs:
        st.info("Chưa có tenant config.")
    else:
        st.dataframe(
            [
                {
                    "tenant_id": tenant_id,
                    "display_name": cfg.get("display_name", tenant_id),
                    "model_name": cfg.get("model_name", "llama3"),
                    "adapter_name": cfg.get("adapter_name", "base"),
                    "top_k": cfg.get("top_k", 4),
                    "memory_turns": cfg.get("memory_turns", 6),
                }
                for tenant_id, cfg in sorted(tenant_configs.items())
            ],
            use_container_width=True,
        )

    st.markdown("### Cập nhật tenant hiện tại")
    current_cfg = tenant_configs.get(selected_tenant, {})
    with st.form("tenant_update_form"):
        display_name = st.text_input("Display name", value=current_cfg.get("display_name", selected_tenant))
        model_name = st.text_input("Model name", value=current_cfg.get("model_name", "llama3"))
        adapter_name = st.text_input("Adapter name", value=current_cfg.get("adapter_name", "base"))
        top_k = st.number_input("Top K", min_value=1, max_value=20, value=int(current_cfg.get("top_k", 4)))
        memory_turns = st.number_input(
            "Memory turns",
            min_value=1,
            max_value=30,
            value=int(current_cfg.get("memory_turns", 6)),
        )
        language_hint = st.text_input(
            "Language hint",
            value=current_cfg.get("language_hint", "Tự động theo ngôn ngữ câu hỏi"),
        )
        persona = st.text_area(
            "Persona",
            value=current_cfg.get("persona", "Bạn là trợ lý tư vấn doanh nghiệp."),
            height=120,
        )
        submitted = st.form_submit_button("Lưu tenant config")
        if submitted:
            tenant_configs[selected_tenant] = {
                "display_name": display_name.strip() or selected_tenant,
                "persona": persona.strip(),
                "language_hint": language_hint.strip() or "Tự động",
                "top_k": int(top_k),
                "memory_turns": int(memory_turns),
                "model_name": model_name.strip() or "llama3",
                "adapter_name": adapter_name.strip() or "base",
            }
            save_tenant_configs(tenant_configs)
            st.success("Đã lưu tenants.json.")

    st.markdown("### Tạo tenant mới")
    with st.form("tenant_create_form"):
        raw_tenant_id = st.text_input("Tenant ID mới (text tự do)")
        tenant_display = st.text_input("Display name tenant mới")
        create_submitted = st.form_submit_button("Tạo tenant")
        if create_submitted:
            tenant_id = normalize_tenant_id(raw_tenant_id.strip())
            if tenant_id in tenant_configs:
                st.warning(f"Tenant `{tenant_id}` đã tồn tại.")
            else:
                tenant_configs[tenant_id] = {
                    "display_name": tenant_display.strip() or tenant_id,
                    "persona": "Bạn là trợ lý tư vấn doanh nghiệp.",
                    "language_hint": "Tự động theo ngôn ngữ câu hỏi",
                    "top_k": 5,
                    "memory_turns": 6,
                    "model_name": "llama3",
                    "adapter_name": "base",
                }
                save_tenant_configs(tenant_configs)
                st.success(f"Đã tạo tenant `{tenant_id}`. Reload trang để thấy trong dropdown.")

with tab_lora:
    st.subheader("Không gian LoRA")
    st.caption("Upload dữ liệu `.txt`, chạy pipeline1, rồi theo dõi số bản ghi sinh ra cho bước huấn luyện adapter.")

    ensure_data_dir()

    uploader = st.file_uploader(
        "Upload tài liệu txt cho pipeline1",
        type=["txt"],
        accept_multiple_files=True,
    )
    if uploader:
        saved = 0
        for item in uploader:
            target = DATA_FILES_DIR / item.name
            target.write_bytes(item.getbuffer())
            saved += 1
        st.success(f"Đã lưu {saved} file vào {DATA_FILES_DIR}.")

    txt_files: List[Path] = sorted(DATA_FILES_DIR.glob("*.txt"))
    st.markdown("### Danh sách file nguồn hiện có")
    if txt_files:
        st.dataframe(
            [{"file": p.name, "size_kb": round(p.stat().st_size / 1024, 2)} for p in txt_files],
            use_container_width=True,
        )
    else:
        st.info("Chưa có file txt trong data/files.")

    if st.button("Chạy pipeline1 (generate QA + export LoRA)", use_container_width=True):
        with st.spinner("Đang chạy pipeline1..."):
            code, output = run_pipeline1()
        if code == 0:
            st.success("Pipeline1 chạy thành công.")
        else:
            st.error(f"Pipeline1 lỗi (exit code {code}).")
        st.code(output or "(không có output)", language="text")

    st.markdown("### Tình trạng dataset")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("generated_qa.json records", count_json_records(GENERATED_QA_PATH))
        st.caption(str(GENERATED_QA_PATH))
    with col_b:
        st.metric("lora_dataset.json records", count_json_records(LORA_DATASET_PATH))
        st.caption(str(LORA_DATASET_PATH))

    st.markdown(
        "Gợi ý bước tiếp theo: dùng `lora_dataset.json` để train adapter riêng cho từng tenant, "
        "sau đó cập nhật `adapter_name` trong cấu hình tenant."
    )
