from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from project_root.ingestion import (
    list_real_files,
    read_links,
    selected_shared_files_dir,
    selected_shared_links_file,
    tenant_files_dir,
    tenant_links_file,
)
from project_root.tools import (
    _dataset_kind,
    _group_columns,
    _read_excel_sheet_clean,
    _read_csv_clean,
    _sample_values,
)

TENANTS_DIR = BASE_DIR / "data" / "tenants"
DEFAULT_OUTPUT = BASE_DIR / "evaluation" / "test_queries.json"
SUPPORTED_FILE_SUFFIXES = {".pdf", ".txt", ".md", ".xlsx", ".xls", ".csv", ".docx"}

STOPWORDS = {
    "và", "là", "của", "cho", "trong", "được", "với", "các", "một", "những", "này", "đó",
    "the", "and", "for", "with", "from", "this", "that", "are", "was", "were", "file",
    "pdf", "xlsx", "xls", "csv", "txt", "md", "docx", "doc", "https", "http", "www", "com",
}


@dataclass
class SourceItem:
    tenant_id: str
    path_or_url: str
    kind: str
    source_name: str


def _normalize_text(text: str) -> str:
    return " ".join(str(text).replace("\n", " ").replace("\r", " ").split()).strip()


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    return s.strip("_") or "item"


def _top_keywords(text: str, limit: int = 8) -> List[str]:
    words = re.findall(r"\b[\wÀ-ỹ-]+\b", text.lower())
    words = [w for w in words if len(w) >= 4 and w not in STOPWORDS and not w.isdigit()]
    return [word for word, _ in Counter(words).most_common(limit)]


def _difficulty_for_index(index: int) -> str:
    if index < 2:
        return "easy"
    if index < 4:
        return "medium"
    return "hard"


def _category_for_path(path_or_url: str, kind: str) -> str:
    lowered = path_or_url.lower()
    if kind == "link":
        return "web_content"
    if any(token in lowered for token in ["qcdt", "quy_che", "quy chế", "regulation"]):
        return "regulation"
    if any(token in lowered for token in ["tkb", "thoi_khoa_bieu", "schedule"]):
        return "timetable"
    if lowered.endswith((".xlsx", ".xls", ".csv")):
        return "table_data"
    return "document"


def _scan_workspace_sources() -> List[SourceItem]:
    items: List[SourceItem] = []

    shared_dir = selected_shared_files_dir()
    if shared_dir:
        for path in list_real_files(shared_dir):
            if path.suffix.lower() in SUPPORTED_FILE_SUFFIXES:
                items.append(SourceItem("default", str(path), "file", path.name))

    shared_links = selected_shared_links_file()
    if shared_links:
        for url in read_links(shared_links):
            items.append(SourceItem("default", url, "link", url))

    if TENANTS_DIR.exists():
        for tenant_dir in sorted(p for p in TENANTS_DIR.iterdir() if p.is_dir()):
            tenant_id = tenant_dir.name
            for path in list_real_files(tenant_files_dir(tenant_id)):
                if path.suffix.lower() in SUPPORTED_FILE_SUFFIXES:
                    items.append(SourceItem(tenant_id, str(path), "file", path.name))
            for url in read_links(tenant_links_file(tenant_id)):
                items.append(SourceItem(tenant_id, url, "link", url))

    return items


def _resolve_explicit_sources(files: Sequence[str], links: Sequence[str], tenant_id: str) -> List[SourceItem]:
    items: List[SourceItem] = []
    for value in files:
        path = Path(value).expanduser().resolve()
        items.append(SourceItem(tenant_id, str(path), "file", path.name))
    for url in links:
        items.append(SourceItem(tenant_id, url, "link", url))
    return items


def build_source_items(files: Sequence[str], links: Sequence[str], tenant_id: str) -> List[SourceItem]:
    return _resolve_explicit_sources(files, links, tenant_id)


def _read_pdf_preview(path: Path, max_pages: int = 4) -> str:
    reader = PdfReader(str(path))
    chunks = [(page.extract_text() or "") for page in reader.pages[:max_pages]]
    return _normalize_text(" ".join(chunks))


def _read_docx_preview(path: Path, max_paragraphs: int = 30) -> str:
    if not importlib.util.find_spec("docx"):
        raise RuntimeError("python-docx chưa được cài")
    from docx import Document  # type: ignore

    doc = Document(str(path))
    paragraphs = [_normalize_text(p.text) for p in doc.paragraphs[:max_paragraphs] if _normalize_text(p.text)]
    return _normalize_text(" ".join(paragraphs))


def _read_text_preview(path: Path, max_chars: int = 4000) -> str:
    return _normalize_text(path.read_text(encoding="utf-8", errors="ignore")[:max_chars])


def _best_excel_table(path: Path) -> tuple[pd.DataFrame, str, str]:
    if path.suffix.lower() == ".csv":
        df, _, title = _read_csv_clean(path)
        return df, path.stem, title

    workbook = pd.ExcelFile(path)
    best_df = pd.DataFrame()
    best_sheet = workbook.sheet_names[0]
    best_title = ""
    best_score = float("-inf")

    for sheet in workbook.sheet_names:
        try:
            df, _, title = _read_excel_sheet_clean(path, sheet)
            if df.empty:
                continue
            score = len(df.columns) + min(len(df), 500) / 500.0
            if score > best_score:
                best_score = score
                best_df = df
                best_sheet = sheet
                best_title = title
        except Exception:
            continue

    return best_df, best_sheet, best_title


def _read_link_preview(url: str, timeout: float = 10.0) -> str:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = _normalize_text(soup.title.get_text(" ", strip=True) if soup.title else "")
    body = _normalize_text(" ".join(tag.get_text(" ", strip=True) for tag in soup.find_all(["h1", "h2", "h3", "p"])[:24]))
    return _normalize_text(f"{title} {body}")


def _queries_for_document(source: SourceItem, preview: str) -> List[dict]:
    keywords = _top_keywords(preview, limit=8)
    first = keywords[:3] or ["nội dung"]
    questions = [
        f"Tài liệu {source.source_name} nói về nội dung chính gì?",
        f"Tài liệu {source.source_name} có nhắc đến {first[0]} không?",
        f"Các chủ đề nổi bật trong {source.source_name} là gì?",
        f"Hãy tóm tắt ngắn tài liệu {source.source_name}.",
        f"Tài liệu {source.source_name} có thông tin nào liên quan đến {first[min(1, len(first)-1)]}?",
        f"Trong {source.source_name}, thông tin nào liên quan đến {first[min(2, len(first)-1)]}?",
    ]
    return [
        {
            "query": q,
            "expected_route": "retrieval",
            "category": _category_for_path(source.path_or_url, source.kind),
            "difficulty": _difficulty_for_index(i),
            "relevant_docs": [source.source_name],
            "expected_keywords": keywords[:5],
            "notes": "auto-generated from document preview",
        }
        for i, q in enumerate(questions)
    ]


def _queries_for_table(source: SourceItem, path: Path) -> List[dict]:
    df, sheet_name, title = _best_excel_table(path)
    if df.empty:
        raise RuntimeError("Không đọc được bảng dữ liệu rõ ràng")

    columns = [str(c) for c in df.columns.tolist()]
    kind = _dataset_kind(title, columns, path)
    groups = _group_columns(columns)
    course_examples = _sample_values(df, ["ten_hp", "ten_hoc_phan", "tên_hp"], limit=3)
    unit_examples = _sample_values(df, ["truong_vien_khoa", "vien", "khoa"], limit=2)
    first_row = df.head(1).fillna("").astype(str).to_dict(orient="records")
    sample_pairs = list(first_row[0].items())[:4] if first_row else []

    questions = [
        f"File {source.source_name} thuộc loại dữ liệu gì?",
        f"File {source.source_name} có những cột dữ liệu chính nào?",
        f"Sheet `{sheet_name}` của {source.source_name} đang lưu các nhóm thông tin nào?",
    ]

    for value in course_examples[:2]:
        questions.append(f"Trong file {source.source_name}, có thông tin nào về học phần `{value}`?")
    for value in unit_examples[:1]:
        questions.append(f"File {source.source_name} có dữ liệu nào liên quan đến đơn vị `{value}`?")
    if sample_pairs:
        col, value = sample_pairs[0]
        questions.append(f"Trong file {source.source_name}, trường `{col}` có giá trị mẫu như `{value}` không?")

    expected_keywords = columns[:4] + _top_keywords(" ".join(groups + course_examples + unit_examples + [kind]), limit=4)
    return [
        {
            "query": q,
            "expected_route": "tool",
            "category": _category_for_path(source.path_or_url, source.kind),
            "difficulty": _difficulty_for_index(i),
            "relevant_docs": [source.source_name],
            "expected_keywords": list(dict.fromkeys(expected_keywords))[:6],
            "notes": f"auto-generated from structured table analysis (sheet={sheet_name})",
        }
        for i, q in enumerate(questions)
    ]


def _queries_for_link(source: SourceItem, preview: str) -> List[dict]:
    keywords = _top_keywords(preview, limit=8)
    first = keywords[:3] or ["nội dung"]
    questions = [
        f"Link {source.source_name} nói về nội dung chính gì?",
        f"Trang {source.source_name} có nhắc đến {first[0]} không?",
        f"Tóm tắt ngắn nội dung của link {source.source_name}.",
        f"Thông tin nổi bật trên {source.source_name} là gì?",
        f"Link {source.source_name} có nội dung liên quan đến {first[min(1, len(first)-1)]} không?",
        f"Link {source.source_name} có phần nào đề cập đến {first[min(2, len(first)-1)]}?",
    ]
    return [
        {
            "query": q,
            "expected_route": "retrieval",
            "category": "web_content",
            "difficulty": _difficulty_for_index(i),
            "relevant_docs": [source.source_name],
            "expected_keywords": keywords[:5],
            "notes": "auto-generated from web preview",
        }
        for i, q in enumerate(questions)
    ]


def _merge_existing(existing: Sequence[dict], generated: Sequence[dict]) -> List[dict]:
    merged = {str(item.get("id")): item for item in existing if item.get("id")}
    for item in generated:
        merged[str(item["id"])] = item
    return list(merged.values())


def save_generated_queries(
    sources: Sequence[SourceItem],
    output: Path | None = None,
    merge_existing: bool = True,
) -> int:
    output_path = output or DEFAULT_OUTPUT
    queries = generate_queries(sources)

    if merge_existing and output_path.exists():
        existing = json.loads(output_path.read_text(encoding="utf-8"))
        queries = _merge_existing(existing, queries)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(queries)


def generate_queries(sources: Sequence[SourceItem]) -> List[dict]:
    results: List[dict] = []
    seen_ids: set[str] = set()

    for source in sources:
        try:
            if source.kind == "link":
                items = _queries_for_link(source, _read_link_preview(source.path_or_url))
            else:
                path = Path(source.path_or_url)
                suffix = path.suffix.lower()
                if suffix == ".pdf":
                    items = _queries_for_document(source, _read_pdf_preview(path))
                elif suffix == ".docx":
                    items = _queries_for_document(source, _read_docx_preview(path))
                elif suffix in {".txt", ".md"}:
                    items = _queries_for_document(source, _read_text_preview(path))
                elif suffix in {".xlsx", ".xls", ".csv"}:
                    items = _queries_for_table(source, path)
                else:
                    continue
        except Exception as exc:
            items = [
                {
                    "query": f"Tài liệu {source.source_name} chứa nội dung gì?",
                    "expected_route": "retrieval",
                    "category": _category_for_path(source.path_or_url, source.kind),
                    "difficulty": "medium",
                    "relevant_docs": [source.source_name],
                    "expected_keywords": [],
                    "notes": f"fallback after parsing error: {exc}",
                }
            ]

        for index, item in enumerate(items, start=1):
            query_id = f"{_slug(source.tenant_id)}_{_slug(source.source_name)}_{index:02d}"
            while query_id in seen_ids:
                index += 1
                query_id = f"{_slug(source.tenant_id)}_{_slug(source.source_name)}_{index:02d}"
            seen_ids.add(query_id)
            results.append({"id": query_id, "tenant_id": source.tenant_id, **item})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate evaluation queries from local files and/or links.")
    parser.add_argument("--tenant-id", default="default")
    parser.add_argument("--file", action="append", default=[], help="Explicit file path to include. Repeatable.")
    parser.add_argument("--link", action="append", default=[], help="Explicit HTTP/HTTPS link to include. Repeatable.")
    parser.add_argument("--from-workspace", action="store_true", help="Scan data/shared, data/files and tenant folders.")
    parser.add_argument("--merge-existing", action="store_true", help="Merge generated queries with existing output file.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    sources: List[SourceItem] = []
    if args.from_workspace:
        sources.extend(_scan_workspace_sources())
    sources.extend(_resolve_explicit_sources(args.file, args.link, args.tenant_id))

    deduped: List[SourceItem] = []
    seen = set()
    for source in sources:
        key = (source.tenant_id, source.path_or_url, source.kind)
        if key not in seen:
            seen.add(key)
            deduped.append(source)

    output = Path(args.output)
    count = save_generated_queries(deduped, output=output, merge_existing=args.merge_existing)
    print(f"Generated {count} queries into {output}")


if __name__ == "__main__":
    main()
