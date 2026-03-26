from __future__ import annotations

import ast
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup

from project_root.config import load_tenant_configs
from project_root.ingestion import (
    list_real_files,
    read_links,
    selected_shared_files_dir,
    selected_shared_links_file,
    tenant_files_dir,
    tenant_links_file,
)
from project_root.memory_store import MemoryStore
from project_root.models import TenantProfile
from project_root.runtime_manager import RUNTIME_CACHE, build_runtime
from project_root.utils import HAS_PSUTIL, HAS_SCHEDULER, format_ram_usage, get_ram_usage, now_str


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

_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_FILE_HINT_RE = re.compile(r"[\w\-.]+\.(?:xlsx|xls|csv|pdf|docx|doc|txt|md)", re.IGNORECASE)

EXCEL_HEADER_KEYWORDS = {
    "ky", "kỳ", "ma_lop", "mã_lớp", "mã lớp", "ma hp", "mã hp", "mã_học_phần",
    "ten_hp", "tên_hp", "tên học phần", "ten hp tieng anh", "thứ", "thu", "thời_gian",
    "thời gian", "phòng", "trạng_thái", "trạng thái", "loại_lớp", "buổi_số", "buổi số",
    "mã lớp", "mã hp", "tên hp", "tên hp tiếng anh", "trường_viện_khoa", "trường viện khoa",
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


def _normalize_text(text: Any) -> str:
    s = "" if text is None else str(text)
    s = " ".join(s.replace("\n", " ").replace("\r", " ").split()).strip()
    return s


def _normalize_key(text: Any) -> str:
    s = _normalize_text(text).lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("đ", "d")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def _describe_file_question_detected(question: str) -> bool:
    q = question.lower().strip()

    patterns = [
        "file này chứa gì",
        "file này có gì",
        "file này nói về gì",
        "file excel này chứa gì",
        "file excel này có gì",
        "file csv này chứa gì",
        "file csv này có gì",
        "pdf này nói về gì",
        "pdf này chứa gì",
        "link này nói về gì",
        "link này chứa gì",
        "dữ liệu gì",
        "nội dung gì",
        "chứa những gì",
        "có những gì",
        "mô tả file",
        "tóm tắt file",
    ]

    if any(p in q for p in patterns):
        return True

    file_words = ["file", "excel", "csv", "pdf", "link", "url", "tài liệu"]
    intent_words = ["chứa", "có", "nói về", "nội dung", "dữ liệu", "tóm tắt", "mô tả"]

    return any(w in q for w in file_words) and any(w in q for w in intent_words)


def _excel_question_detected(question: str) -> bool:
    q = question.lower()

    if _FILE_HINT_RE.search(question):
        return True

    excel_terms = [
        "excel",
        "xlsx",
        "xls",
        "csv",
        "sheet",
        "bảng tính",
        "cột nào",
        "những cột nào",
        "chứa dữ liệu gì",
        "có dữ liệu gì",
        "dataset",
        "thời khóa biểu",
        "thoi khoa bieu",
        "bao nhiêu lớp",
        "thứ mấy",
        "liệt kê học phần",
        "mã hp",
        "mã học phần",
        "đọc thông tin môn",
        "thông tin của môn",
        "thông tin môn",
        "môn học",
    ]

    if any(term in q for term in excel_terms):
        return True

    if "môn" in q and "http" not in q and "link" not in q:
        return True

    return False


def _link_question_detected(question: str) -> bool:
    q = question.lower()
    if _URL_RE.search(question):
        return True
    link_terms = [
        "link",
        "url",
        "đường link",
        "liên kết",
        "website",
        "web này",
        "trang này",
        "nội dung link",
    ]
    return any(term in q for term in link_terms)


def _extract_keywords_from_text(text: str, top_k: int = 8) -> List[str]:
    stopwords = {
        "và", "là", "của", "cho", "trong", "được", "với", "các", "một", "những",
        "the", "and", "for", "with", "from", "this", "that", "are", "was", "were",
        "http", "https", "www", "com", "org", "net", "pdf", "file", "sheet",
    }
    words = re.findall(r"\b[\wÀ-ỹ]+\b", text.lower())
    words = [w for w in words if len(w) >= 3 and w not in stopwords and not w.isdigit()]
    freq = Counter(words)
    return [w for w, _ in freq.most_common(top_k)]


def _candidate_data_files(profile: TenantProfile) -> List[Path]:
    files: List[Path] = []
    shared_dir = selected_shared_files_dir()
    if shared_dir:
        files.extend(list_real_files(shared_dir))
    files.extend(list_real_files(tenant_files_dir(profile.tenant_id)))
    return files


def _candidate_excel_files(profile: TenantProfile) -> List[Path]:
    return [p for p in _candidate_data_files(profile) if p.suffix.lower() in {".xlsx", ".xls", ".csv"}]


def _choose_target_file(question: str, profile: TenantProfile) -> Optional[Path]:
    files = _candidate_data_files(profile)
    if not files:
        return None

    q = question.lower()

    hinted = re.findall(r"[\w\-.]+\.(?:xlsx|xls|csv|pdf|docx|doc|txt|md)", q, re.IGNORECASE)
    if hinted:
        hinted_lower = [h.lower() for h in hinted]
        for f in files:
            if f.name.lower() in hinted_lower:
                return f

    priority_suffixes: List[str] = []
    if any(k in q for k in ["excel", "xlsx", "xls"]):
        priority_suffixes = [".xlsx", ".xls"]
    elif "csv" in q:
        priority_suffixes = [".csv"]
    elif "pdf" in q:
        priority_suffixes = [".pdf"]

    for suffix in priority_suffixes:
        for f in files:
            if f.suffix.lower() == suffix:
                return f

    return files[0]


def _choose_excel_file(question: str, profile: TenantProfile) -> Optional[Path]:
    files = _candidate_excel_files(profile)
    if not files:
        return None

    q = question.lower()
    hinted = re.findall(r"[\w\-.]+\.(?:xlsx|xls|csv)", q, re.IGNORECASE)
    if hinted:
        hinted_lower = [h.lower() for h in hinted]
        for f in files:
            if f.name.lower() in hinted_lower:
                return f

    for f in files:
        if f.name.lower() in q:
            return f

    return files[0]


def _header_row_score(row_values: List[Any]) -> float:
    cells = [_normalize_text(v) for v in row_values]
    non_empty = [c for c in cells if c]
    if not non_empty:
        return -1.0

    score = len(non_empty) * 1.5
    lowered = [_normalize_key(c) for c in non_empty]

    for cell in lowered:
        if cell in EXCEL_HEADER_KEYWORDS:
            score += 5
        if any(k in cell for k in [
            "ma_lop", "ma_hp", "ten_hp", "ten_hp_tieng_anh", "thoi_gian", "phong",
            "trang_thai", "loai_lop", "buoi_so", "truong_vien_khoa", "khoi_luong",
            "vien", "khoa", "thu",
        ]):
            score += 4
        if re.fullmatch(r"\d{4,}", cell):
            score -= 3
        if len(cell) > 60:
            score -= 2

    joined = " ".join(lowered)
    if "thoi_khoa_bieu" in joined:
        score -= 4
    if "ky" in lowered or "truong_vien_khoa" in lowered:
        score += 2
    return score


def _make_unique_headers(values: List[Any]) -> List[str]:
    used: Dict[str, int] = {}
    headers: List[str] = []
    for idx, value in enumerate(values, start=1):
        raw = _normalize_text(value)
        if not raw:
            raw = f"Unnamed_{idx}"
        base = raw
        count = used.get(base, 0)
        if count:
            raw = f"{base}_{count + 1}"
        used[base] = count + 1
        headers.append(raw)
    return headers


def _read_csv_clean(path: Path) -> Tuple[pd.DataFrame, int, str]:
    df = pd.read_csv(path)
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all").reset_index(drop=True)
    title = path.stem
    return df, 0, title


def _read_excel_sheet_clean(path: Path, sheet_name: str) -> Tuple[pd.DataFrame, int, str]:
    if path.suffix.lower() == ".csv":
        return _read_csv_clean(path)

    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    raw = raw.dropna(axis=1, how="all")
    raw = raw.dropna(axis=0, how="all").reset_index(drop=True)

    if raw.empty:
        return raw, 0, ""

    title = _normalize_text(raw.iloc[0, 0]) if raw.shape[0] > 0 else ""

    candidate_rows = min(len(raw), 12)
    best_idx = 0
    best_score = float("-inf")
    for idx in range(candidate_rows):
        score = _header_row_score(raw.iloc[idx].tolist())
        if score > best_score:
            best_score = score
            best_idx = idx

    headers = _make_unique_headers(raw.iloc[best_idx].tolist())
    df = raw.iloc[best_idx + 1 :].copy().reset_index(drop=True)
    df.columns = headers
    df = df.dropna(axis=0, how="all")

    keep_cols: List[str] = []
    for col in df.columns:
        series = df[col]
        non_null_ratio = 1.0 - float(series.isna().mean()) if len(series) else 0.0
        if str(col).startswith("Unnamed_") and non_null_ratio < 0.2:
            continue
        keep_cols.append(col)
    df = df[keep_cols]

    return df, best_idx, title


def _dataset_kind(title: str, columns: List[str], path: Path) -> str:
    title_key = _normalize_key(title)
    cols_key = [_normalize_key(c) for c in columns]
    joined = " ".join(cols_key)
    name_key = _normalize_key(path.stem)

    if "thoi_khoa_bieu" in title_key or "thoi_khoa_bieu" in name_key:
        match = re.search(r"ky[_ ]?(\d{4,6})", title_key or name_key)
        ky = match.group(1) if match else ""
        return f"thời khóa biểu dự kiến kỳ {ky}".strip()
    if "ma_hp" in joined and ("thu" in joined or "thoi_gian" in joined):
        return "thời khóa biểu / lịch học học phần"
    if "diem" in joined:
        return "bảng điểm hoặc kết quả học tập"
    if "hoc_phi" in joined:
        return "dữ liệu học phí"
    return "dữ liệu bảng nội bộ"


def _group_columns(columns: List[str]) -> List[str]:
    col_keys = {_normalize_key(c): c for c in columns}
    keys = list(col_keys.keys())
    groups: List[str] = []

    def has(*patterns: str) -> bool:
        return any(any(p in key for p in patterns) for key in keys)

    if has("truong_vien_khoa", "vien", "khoa"):
        groups.append("Trường/viện/khoa")
    if has("ma_lop", "ma_lop_kem"):
        groups.append("Mã lớp, mã lớp kèm")
    if has("ma_hp", "ten_hp", "ten_hp_tieng_anh"):
        groups.append("Mã học phần, tên học phần, tên tiếng Anh")
    if has("khoi_luong", "ghi_chu"):
        groups.append("Khối lượng và ghi chú lớp")
    if has("buoi_so", "thu", "thoi_gian", "bd", "kt", "kip", "tuan"):
        groups.append("Lịch học: buổi số, thứ, thời gian, kíp, tuần")
    if has("phong", "can_tn", "sldk", "sl_max", "trang_thai", "loai_lop", "dot_mo"):
        groups.append("Phòng học, chỉ tiêu đăng ký và trạng thái lớp")

    if not groups:
        groups.append("Các cột chính: " + ", ".join(map(str, columns[:6])))

    return groups


def _sample_values(df: pd.DataFrame, col_patterns: List[str], limit: int = 3) -> List[str]:
    target_cols = [c for c in df.columns if any(p in _normalize_key(c) for p in col_patterns)]
    if not target_cols:
        return []

    values: List[str] = []
    for col in target_cols:
        for v in df[col].dropna().astype(str):
            v = _normalize_text(v)
            if not v or v.lower() == "nan":
                continue
            if v not in values:
                values.append(v)
            if len(values) >= limit:
                return values
    return values


def _guess_table_column_roles(columns: List[str]) -> Dict[str, List[str]]:
    roles: Dict[str, List[str]] = {
        "code": [],
        "name": [],
        "category": [],
        "quantity": [],
        "price": [],
        "time": [],
        "location": [],
        "status": [],
        "unit": [],
        "other": [],
    }

    for col in columns:
        key = _normalize_key(col)

        if any(k in key for k in ["ma", "code", "sku", "id"]):
            roles["code"].append(str(col))
        elif any(k in key for k in ["ten", "name", "mo_ta", "description"]):
            roles["name"].append(str(col))
        elif any(k in key for k in ["loai", "nhom", "category", "brand"]):
            roles["category"].append(str(col))
        elif any(k in key for k in ["so_luong", "quantity", "stock", "ton"]):
            roles["quantity"].append(str(col))
        elif any(k in key for k in ["gia", "price", "doanh_thu", "revenue", "cost"]):
            roles["price"].append(str(col))
        elif any(k in key for k in ["ngay", "date", "time", "thoi_gian", "thu", "kip"]):
            roles["time"].append(str(col))
        elif any(k in key for k in ["dia_diem", "chi_nhanh", "store", "location", "phong"]):
            roles["location"].append(str(col))
        elif any(k in key for k in ["trang_thai", "status"]):
            roles["status"].append(str(col))
        elif any(k in key for k in ["vien", "khoa", "unit", "department"]):
            roles["unit"].append(str(col))
        else:
            roles["other"].append(str(col))

    return roles


def _format_table_inspection(path: Path, df: pd.DataFrame, source_name: str, header_note: str = "") -> str:
    if df.empty:
        return f"File `{source_name}` hiện không có dữ liệu bảng đủ rõ để mô tả."

    columns = [str(c) for c in df.columns.tolist()]
    roles = _guess_table_column_roles(columns)

    sample_info: List[str] = []
    for role in ["code", "name", "category", "unit", "quantity", "price", "time", "location", "status"]:
        cols = roles.get(role, [])
        if not cols:
            continue
        col = cols[0]
        vals = []
        for v in df[col].dropna().astype(str):
            v = _normalize_text(v)
            if v and v not in vals:
                vals.append(v)
            if len(vals) >= 3:
                break
        if vals:
            sample_info.append(f"- Cột `{col}` có ví dụ: {', '.join(vals)}")

    keywords = _extract_keywords_from_text(
        " ".join(columns + [str(v) for v in df.head(20).fillna("").astype(str).values.flatten()])
    )

    group_lines: List[str] = []
    if roles["code"]:
        group_lines.append("- Mã/ID")
    if roles["name"]:
        group_lines.append("- Tên/mô tả")
    if roles["category"]:
        group_lines.append("- Nhóm/danh mục")
    if roles["quantity"]:
        group_lines.append("- Số lượng/tồn kho")
    if roles["price"]:
        group_lines.append("- Giá trị/giá bán/doanh thu")
    if roles["time"]:
        group_lines.append("- Thời gian/lịch")
    if roles["location"]:
        group_lines.append("- Địa điểm/chi nhánh/phòng")
    if roles["status"]:
        group_lines.append("- Trạng thái")
    if roles["unit"]:
        group_lines.append("- Đơn vị/phòng ban/viện-khoa")
    if not group_lines:
        group_lines.append("- Các trường dữ liệu tổng quát trong bảng")

    lines: List[str] = []
    lines.append(f"File `{source_name}` là một **bảng dữ liệu có cấu trúc**.")
    lines.append("")
    lines.append(f"- Số dòng dữ liệu: **{len(df):,}**")
    lines.append(f"- Số cột hữu ích: **{len(columns)}**")
    lines.append(f"- Một số cột chính: {', '.join(columns[:12])}")

    if header_note:
        lines.append(f"- Ghi chú đọc file: {header_note}")

    lines.append("")
    lines.append("Dữ liệu trong file có vẻ gồm các nhóm thông tin như:")
    lines.extend(group_lines)

    if keywords:
        lines.append("")
        lines.append("Một số từ khóa nổi bật suy ra từ dữ liệu:")
        lines.append("- " + ", ".join(keywords[:8]))

    if sample_info:
        lines.append("")
        lines.append("Ví dụ giá trị trong bảng:")
        lines.extend(sample_info[:6])

    return "\n".join(lines)


def _inspect_excel_csv(path: Path) -> str:
    try:
        if path.suffix.lower() == ".csv":
            df, _, _ = _read_csv_clean(path)
            return _format_table_inspection(path, df, path.name)

        workbook = pd.ExcelFile(path)
        best_sheet = None
        best_df = None
        best_score = -1
        best_header_note = ""

        for sheet in workbook.sheet_names:
            try:
                df, header_row_idx, _ = _read_excel_sheet_clean(path, sheet)
                if df.empty:
                    continue

                score = len(df.columns) + min(len(df), 1000) / 1000.0
                score += _score_sheet(df, "describe file")

                if score > best_score:
                    best_score = score
                    best_sheet = sheet
                    best_df = df
                    best_header_note = (
                        f"đã chọn sheet `{sheet}` làm sheet đại diện"
                        + (
                            f", tự bỏ qua khoảng {header_row_idx} dòng tiêu đề/phụ đề ở đầu"
                            if header_row_idx > 0 else ""
                        )
                    )
            except Exception:
                continue

        if best_df is None or best_df.empty:
            return f"File Excel `{path.name}` chưa trích xuất được dữ liệu bảng rõ ràng."

        result = _format_table_inspection(path, best_df, path.name, best_header_note)

        if len(workbook.sheet_names) > 1:
            result += f"\n\nNgoài ra file còn **{len(workbook.sheet_names)} sheet**: " + ", ".join(workbook.sheet_names[:10])

        return result
    except Exception as exc:
        return f"Lỗi khi phân tích file bảng `{path.name}`: {exc}"


def _inspect_pdf(path: Path) -> str:
    try:
        import pypdf

        reader = pypdf.PdfReader(str(path))
        page_count = len(reader.pages)

        extracted_pages: List[str] = []
        for page in reader.pages[:5]:
            try:
                extracted_pages.append(page.extract_text() or "")
            except Exception:
                continue

        text = "\n".join(extracted_pages)
        text = " ".join(text.split())
        if not text:
            return f"File PDF `{path.name}` có {page_count} trang nhưng chưa trích xuất được nội dung văn bản."

        title_candidates = re.findall(r"[A-ZÀ-Ỹ][^\n]{10,120}", text[:1000])
        title = title_candidates[0].strip() if title_candidates else path.stem

        keywords = _extract_keywords_from_text(text, top_k=10)
        preview = text[:1200]

        lines = [
            f"File PDF `{path.name}` là một **tài liệu văn bản** gồm khoảng **{page_count} trang**.",
            "",
            f"- Tiêu đề/gợi ý nội dung chính: **{title}**",
        ]
        if keywords:
            lines.append(f"- Từ khóa nổi bật: {', '.join(keywords[:10])}")
        lines.extend([
            "",
            "Đoạn nội dung đại diện trích từ tài liệu:",
            preview,
        ])
        return "\n".join(lines)
    except Exception as exc:
        return f"Lỗi khi phân tích PDF `{path.name}`: {exc}"


def _inspect_generic_text_file(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        text = " ".join(text.split())
        if not text:
            return f"File `{path.name}` không có nội dung văn bản rõ ràng."

        keywords = _extract_keywords_from_text(text, top_k=10)
        lines = [
            f"File `{path.name}` là một **tệp văn bản**.",
            "",
            f"- Độ dài ước lượng: **{len(text):,} ký tự**",
        ]
        if keywords:
            lines.append(f"- Từ khóa nổi bật: {', '.join(keywords[:10])}")
        lines.extend([
            "",
            "Đoạn nội dung đại diện:",
            text[:1200],
        ])
        return "\n".join(lines)
    except Exception as exc:
        return f"Lỗi khi đọc file văn bản `{path.name}`: {exc}"


def _format_excel_summary(path: Path) -> str:
    try:
        if path.suffix.lower() == ".csv":
            df, _, title = _read_csv_clean(path)
            if df.empty:
                return f"File CSV {path.name} không có dữ liệu để phân tích."

            columns = list(df.columns)
            kind = _dataset_kind(title, columns, path)
            groups = _group_columns(columns)

            lines: List[str] = []
            lines.append(f"File CSV này chứa **{kind}**.")
            lines.append("")
            lines.append("Dữ liệu gồm các nhóm thông tin chính như:")
            for group in groups:
                lines.append(f"- {group}")
            lines.append("")
            lines.append(f"File hiện có khoảng **{len(df):,} dòng dữ liệu** và **{len(columns)} cột hữu ích**.")
            return "\n".join(lines).strip()

        workbook = pd.ExcelFile(path)
        sheet_names = workbook.sheet_names
        if not sheet_names:
            return f"File Excel {path.name} không có sheet nào để phân tích."

        sheet_summaries: List[str] = []
        primary_df: Optional[pd.DataFrame] = None
        primary_title = ""
        primary_header_row = 0
        primary_sheet = sheet_names[0]

        for sheet in sheet_names[:5]:
            try:
                df, header_row_idx, title = _read_excel_sheet_clean(path, sheet)
            except Exception as exc:
                sheet_summaries.append(f"- Sheet '{sheet}': không đọc được ({exc})")
                continue

            if primary_df is None and not df.empty:
                primary_df = df
                primary_title = title
                primary_header_row = header_row_idx
                primary_sheet = sheet

            sheet_summaries.append(f"- Sheet '{sheet}': {len(df):,} dòng dữ liệu, {len(df.columns)} cột hữu ích")

        if primary_df is None or primary_df.empty:
            return (
                f"Mình đã mở file Excel {path.name}, nhưng chưa trích xuất được dữ liệu dạng bảng rõ ràng. "
                f"Bạn có thể chỉ rõ tên sheet hoặc cho mình chuẩn hóa lại file."
            )

        columns = list(primary_df.columns)
        kind = _dataset_kind(primary_title, columns, path)
        groups = _group_columns(columns)
        course_examples = _sample_values(primary_df, ["ten_hp", "ten_hoc_phan"], limit=3)
        unit_examples = _sample_values(primary_df, ["truong_vien_khoa", "vien", "khoa"], limit=3)

        lines: List[str] = []
        if kind.startswith("thời khóa biểu"):
            lines.append(f"File Excel này chứa **{kind}**.")
        else:
            lines.append(f"File Excel này chủ yếu chứa **{kind}**.")

        lines.append("")
        lines.append("Dữ liệu gồm các nhóm thông tin chính như:")
        for group in groups:
            lines.append(f"- {group}")

        if course_examples:
            lines.append("")
            lines.append("Một vài học phần xuất hiện trong dữ liệu:")
            for item in course_examples:
                lines.append(f"- {item}")

        if unit_examples:
            lines.append("")
            lines.append("Đơn vị/viện khoa xuất hiện trong dữ liệu, ví dụ:")
            for item in unit_examples:
                lines.append(f"- {item}")

        lines.append("")
        lines.append(
            f"Sheet chính `{primary_sheet}` hiện có khoảng **{len(primary_df):,} dòng dữ liệu** và **{len(columns)} cột hữu ích**."
        )

        if primary_header_row > 0:
            lines.append(
                f"Mình đã tự bỏ qua khoảng **{primary_header_row} dòng tiêu đề/phụ đề ở đầu sheet** để đọc đúng hàng tiêu đề hơn."
            )

        unnamed_cols = [c for c in columns if _normalize_key(c).startswith("unnamed")]
        if unnamed_cols:
            lines.append(
                "Vẫn còn một số cột chưa có tên rõ ràng, nên nếu bạn muốn trích chính xác từng trường thì nên chuẩn hóa lại header của file."
            )

        if len(sheet_names) > 1:
            lines.append("")
            lines.append(f"Ngoài ra file còn **{len(sheet_names)} sheet**. Tóm tắt nhanh:")
            lines.extend(sheet_summaries)

        return "\n".join(lines).strip()
    except Exception as exc:
        return f"Lỗi khi đọc file Excel/CSV '{path.name}': {exc}"


def _excel_query_detect(question: str) -> Optional[Dict[str, Any]]:
    q = question.lower()

    if "bao nhiêu lớp" in q:
        m = re.search(r"([a-z]{2,}\d{2,})", q)
        if m:
            return {"type": "count", "code": m.group(1).upper()}

        m_name = re.search(r"bao nhiêu lớp của môn\s+(.+)", q)
        if m_name:
            return {"type": "count_name", "name": m_name.group(1).strip()}

    if "thứ mấy" in q or ("học vào" in q and "thứ" in q):
        m = re.search(r"([a-z]{2,}\d{2,})", q)
        if m:
            return {"type": "day", "code": m.group(1).upper()}

        m_name = re.search(r"môn\s+(.+?)\s+(?:học vào|học).*", q)
        if m_name:
            return {"type": "day_name", "name": m_name.group(1).strip()}

    if "đọc thông tin" in q or "thông tin của môn" in q or "thông tin môn" in q:
        m_name = re.search(r"môn\s+(.+)", q)
        if m_name:
            return {"type": "info_name", "name": m_name.group(1).strip()}

    if "liệt kê" in q and ("viện" in q or "khoa" in q):
        unit_match = re.search(r"(?:viện|khoa)\s+([^\n,.;:]+)", q)
        unit = unit_match.group(1).strip() if unit_match else None
        return {"type": "list_unit", "unit": unit}

    if ("học phần" in q or "môn" in q) and ("viện" in q or "khoa" in q):
        unit_match = re.search(r"(?:viện|khoa)\s+([^\n,.;:]+)", q)
        unit = unit_match.group(1).strip() if unit_match else None
        return {"type": "list_unit", "unit": unit}

    return None


def _find_column(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
    for col in df.columns:
        key = _normalize_key(col)
        if any(k in key for k in keywords):
            return col
    return None


def _score_sheet(df: pd.DataFrame, question: str) -> int:
    score = 0
    q = question.lower()

    for col in df.columns:
        col_lower = str(col).lower()
        if any(k in col_lower for k in ["mã", "ma"]):
            score += 2
        if any(k in col_lower for k in ["tên", "ten"]):
            score += 2
        if any(k in col_lower for k in ["thứ", "thu"]):
            score += 2
        if any(k in col_lower for k in ["viện", "khoa"]):
            score += 2
        if any(k in col_lower for k in ["phòng", "phong", "kíp", "kip", "thời gian", "thoi"]):
            score += 1

    if re.search(r"[a-z]{2,}\d{2,}", q):
        score += 2
    if "lớp" in q:
        score += 1
    if "học phần" in q or "môn" in q:
        score += 1

    return score


def _select_best_sheet(path: Path, question: str) -> Tuple[Optional[str], Optional[pd.DataFrame]]:
    if path.suffix.lower() == ".csv":
        df, _, _ = _read_csv_clean(path)
        return path.stem, df

    workbook = pd.ExcelFile(path)

    best_score = -1
    best_sheet: Optional[str] = None
    best_df: Optional[pd.DataFrame] = None

    for sheet in workbook.sheet_names:
        try:
            df, _, _ = _read_excel_sheet_clean(path, sheet)
            if df.empty:
                continue

            score = _score_sheet(df, question)
            if score > best_score:
                best_score = score
                best_sheet = sheet
                best_df = df
        except Exception:
            continue

    return best_sheet, best_df


def _filter_contains(df: pd.DataFrame, col: str, value: str) -> pd.DataFrame:
    return df[df[col].astype(str).str.contains(value, case=False, na=False)]


def _run_excel_query(df: pd.DataFrame, query: Dict[str, Any]) -> str:
    ma_hp_col = _find_column(df, ["ma_hp", "ma_hoc_phan", "mã_hp", "mã_học_phần", "mahp"])
    thu_col = _find_column(df, ["thu", "thứ"])
    unit_col = _find_column(df, ["truong_vien_khoa", "vien", "khoa"])
    ten_hp_col = _find_column(df, ["ten_hp", "ten_hoc_phan", "tên_hp", "tên_học_phần", "ten"])
    ma_lop_col = _find_column(df, ["ma_lop", "mã_lớp"])
    thoi_gian_col = _find_column(df, ["thoi_gian", "thời_gian", "thời_gian_học", "gio", "kip"])
    phong_col = _find_column(df, ["phong", "phòng"])

    if query["type"] == "count":
        code = query["code"]
        if not ma_hp_col:
            return "Không tìm thấy cột mã học phần."
        subset = _filter_contains(df, ma_hp_col, code)
        if subset.empty:
            return f"Không tìm thấy dữ liệu cho môn {code}."
        if ma_lop_col:
            class_count = subset[ma_lop_col].astype(str).nunique()
            return f"Môn {code} có khoảng {class_count} lớp phân biệt."
        return f"Môn {code} có khoảng {len(subset)} dòng/lớp trong dữ liệu."

    if query["type"] == "count_name":
        name = query["name"]
        if not ten_hp_col:
            return "Không tìm thấy cột tên học phần."
        subset = _filter_contains(df, ten_hp_col, name)
        if subset.empty:
            return f"Không tìm thấy dữ liệu cho môn '{name}'."
        if ma_lop_col:
            class_count = subset[ma_lop_col].astype(str).nunique()
            return f"Môn '{name}' có khoảng {class_count} lớp phân biệt."
        return f"Môn '{name}' có khoảng {len(subset)} dòng/lớp trong dữ liệu."

    if query["type"] == "day":
        code = query["code"]
        if not ma_hp_col:
            return "Không tìm thấy cột mã học phần."
        subset = _filter_contains(df, ma_hp_col, code)
        if subset.empty:
            return f"Không tìm thấy dữ liệu cho môn {code}."
        if not thu_col:
            return f"Đã tìm thấy môn {code} nhưng chưa xác định được cột thứ học."

        days = [str(x) for x in subset[thu_col].dropna().astype(str).unique().tolist()]
        if not days:
            return f"Đã tìm thấy môn {code} nhưng chưa có dữ liệu về thứ học."

        extra_parts: List[str] = []
        if thoi_gian_col:
            times = [str(x) for x in subset[thoi_gian_col].dropna().astype(str).unique().tolist()[:5]]
            if times:
                extra_parts.append("thời gian/ca học: " + ", ".join(times))
        if phong_col:
            rooms = [str(x) for x in subset[phong_col].dropna().astype(str).unique().tolist()[:5]]
            if rooms:
                extra_parts.append("phòng học: " + ", ".join(rooms))

        answer = f"Môn {code} học vào các ngày/thứ: {', '.join(days)}."
        if extra_parts:
            answer += " Ngoài ra có " + "; ".join(extra_parts) + "."
        return answer

    if query["type"] == "day_name":
        name = query["name"]
        if not ten_hp_col:
            return "Không tìm thấy cột tên học phần."
        subset = _filter_contains(df, ten_hp_col, name)
        if subset.empty:
            return f"Không tìm thấy dữ liệu cho môn '{name}'."
        if not thu_col:
            return f"Đã tìm thấy môn '{name}' nhưng chưa xác định được cột thứ học."

        days = [str(x) for x in subset[thu_col].dropna().astype(str).unique().tolist()]
        answer = f"Môn '{name}' học vào các ngày/thứ: {', '.join(days)}."
        if thoi_gian_col:
            times = [str(x) for x in subset[thoi_gian_col].dropna().astype(str).unique().tolist()[:5]]
            if times:
                answer += " Thời gian/ca học: " + ", ".join(times) + "."
        return answer

    if query["type"] == "info_name":
        name = query["name"]
        if not ten_hp_col:
            return "Không tìm thấy cột tên học phần."
        subset = _filter_contains(df, ten_hp_col, name)
        if subset.empty:
            return f"Không tìm thấy dữ liệu cho môn '{name}'."

        lines = [f"Thông tin tìm thấy cho môn '{name}':"]

        if ma_hp_col:
            codes = [str(x) for x in subset[ma_hp_col].dropna().astype(str).unique().tolist()[:5]]
            if codes:
                lines.append(f"- Mã học phần: {', '.join(codes)}")

        if ma_lop_col:
            classes = [str(x) for x in subset[ma_lop_col].dropna().astype(str).unique().tolist()[:10]]
            if classes:
                lines.append(f"- Các mã lớp: {', '.join(classes)}")

        if thu_col:
            days = [str(x) for x in subset[thu_col].dropna().astype(str).unique().tolist()[:10]]
            if days:
                lines.append(f"- Học vào các ngày/thứ: {', '.join(days)}")

        if thoi_gian_col:
            times = [str(x) for x in subset[thoi_gian_col].dropna().astype(str).unique().tolist()[:10]]
            if times:
                lines.append(f"- Thời gian/ca học: {', '.join(times)}")

        if phong_col:
            rooms = [str(x) for x in subset[phong_col].dropna().astype(str).unique().tolist()[:10]]
            if rooms:
                lines.append(f"- Phòng học: {', '.join(rooms)}")

        return "\n".join(lines)

    if query["type"] == "list_unit":
        if not unit_col or not ten_hp_col:
            return "Không tìm thấy cột viện/khoa hoặc học phần."
        subset = df
        unit = query.get("unit")
        if unit:
            subset = _filter_contains(df, unit_col, unit)
            if subset.empty:
                return f"Không tìm thấy dữ liệu cho viện/khoa '{unit}'."

        units = [str(x) for x in subset[unit_col].dropna().astype(str).unique().tolist()[:10]]
        subjects = [str(x) for x in subset[ten_hp_col].dropna().astype(str).unique().tolist()[:20]]

        lines: List[str] = []
        if unit:
            lines.append(f"Các học phần tìm thấy cho viện/khoa '{unit}':")
        else:
            lines.append("Một số viện/khoa xuất hiện trong dữ liệu:")
            for u in units[:5]:
                lines.append(f"- {u}")
            lines.append("")
            lines.append("Một số học phần tiêu biểu:")

        for s in subjects[:10]:
            lines.append(f"- {s}")
        return "\n".join(lines)

    return "Không xử lý được truy vấn."


def _run_excel_query_multi(path: Path, question: str, query: Dict[str, Any]) -> str:
    selected_sheet, df = _select_best_sheet(path, question)

    if df is None or df.empty:
        return "Không tìm thấy sheet phù hợp để xử lý dữ liệu."

    result = _run_excel_query(df, query)
    if "Không tìm thấy" not in result and "không tìm thấy" not in result:
        if selected_sheet and path.suffix.lower() != ".csv":
            return f"[Sheet: {selected_sheet}]\n{result}"
        return result

    if path.suffix.lower() != ".csv":
        workbook = pd.ExcelFile(path)
        for sheet in workbook.sheet_names:
            if sheet == selected_sheet:
                continue
            try:
                df2, _, _ = _read_excel_sheet_clean(path, sheet)
                if df2.empty:
                    continue
                result2 = _run_excel_query(df2, query)
                if "Không tìm thấy" not in result2 and "không tìm thấy" not in result2:
                    return f"[Sheet: {sheet}]\n{result2}"
            except Exception:
                continue

    return result


def tool_describe_excel(profile: TenantProfile, question: str) -> str:
    path = _choose_excel_file(question, profile)
    if path is None:
        return "Hiện chưa tìm thấy file Excel/CSV nào trong dữ liệu shared hoặc tenant để phân tích."

    query = _excel_query_detect(question)
    if query:
        return _run_excel_query_multi(path, question, query)

    return _format_excel_summary(path)


def _extract_target_url(question: str, profile: TenantProfile) -> Optional[str]:
    m = _URL_RE.search(question)
    if m:
        return m.group(0).rstrip(").,;]}>")

    tenant_urls = read_links(tenant_links_file(profile.tenant_id))
    shared_urls = read_links(selected_shared_links_file())
    urls = tenant_urls + [u for u in shared_urls if u not in tenant_urls]
    return urls[0] if urls else None


def tool_describe_link(profile: TenantProfile, question: str) -> str:
    url = _extract_target_url(question, profile)
    if not url:
        return "Không tìm thấy đường link nào để phân tích. Bạn có thể gửi trực tiếp URL hoặc thêm link vào links.txt."

    try:
        resp = requests.get(
            url,
            timeout=12,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
        text = " ".join(soup.get_text(separator=" ").split())
        text = text[:2500]

        if not text:
            return f"Đã truy cập link {url} nhưng không trích xuất được nội dung văn bản."

        lines = [f"Link: {url}"]
        if title:
            lines.append(f"Tiêu đề: {title}")
        lines.append("Tóm tắt nội dung thô đã trích xuất:")
        lines.append(text)
        return "\n".join(lines)
    except Exception as exc:
        return f"Lỗi khi đọc link '{url}': {exc}"


def tool_describe_any_file(profile: TenantProfile, question: str) -> str:
    path = _choose_target_file(question, profile)

    if path is None:
        if _link_question_detected(question):
            return tool_describe_link(profile, question)
        return "Hiện chưa tìm thấy file hoặc link nào trong dữ liệu để mô tả."

    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls", ".csv"}:
        return _inspect_excel_csv(path)
    if suffix == ".pdf":
        return _inspect_pdf(path)
    if suffix in {".txt", ".md"}:
        return _inspect_generic_text_file(path)

    return f"Đã nhận diện file `{path.name}` nhưng hiện chưa có inspector chuyên biệt cho định dạng `{suffix}`."


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

    if _describe_file_question_detected(question):
        return tool_describe_any_file(profile, question)

    if _excel_question_detected(question):
        return tool_describe_excel(profile, question)

    if _link_question_detected(question):
        return tool_describe_link(profile, question)

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
        from project_root.llm_service import get_or_create_profile
        new_profile = get_or_create_profile(new_tenant)
        return new_profile, new_user, f"Đã chuyển sang Tenant: {new_tenant}, User: {new_user}"

    if q_lower == "/sources on":
        state["show_sources"] = True
        return profile, user_id, "Đã bật hiển thị nguồn."

    if q_lower == "/sources off":
        state["show_sources"] = False
        return profile, user_id, "Đã tắt hiển thị nguồn."

    return profile, user_id, "Lệnh không hợp lệ. Gõ /help để xem danh sách."
