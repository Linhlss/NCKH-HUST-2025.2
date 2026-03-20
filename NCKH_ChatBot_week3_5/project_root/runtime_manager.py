from __future__ import annotations

import gc
import json
import logging
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict

import chromadb
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DEFAULT_EMBED_MODEL,
    OLLAMA_TIMEOUT,
    STORAGE_ROOT,
)
from ingestion import collect_documents, compute_data_signature
from models import TenantProfile, TenantRuntime
from utils import format_ram_usage, get_ram_usage, now_str

logger = logging.getLogger(__name__)

RUNTIME_CACHE: Dict[str, TenantRuntime] = {}


def tenant_storage_dir(tenant_id: str) -> Path:
    p = STORAGE_ROOT / tenant_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def tenant_chroma_dir(tenant_id: str) -> Path:
    p = tenant_storage_dir(tenant_id) / "chroma_db"
    p.mkdir(parents=True, exist_ok=True)
    return p


def tenant_meta_file(tenant_id: str) -> Path:
    return tenant_storage_dir(tenant_id) / "index_meta.json"


def _create_vector_components(chroma_dir: Path, collection_name: str):
    db = chromadb.PersistentClient(path=str(chroma_dir))
    coll = db.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=coll)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return db, coll, vector_store, storage_context


def _safe_remove_dir(path: Path) -> None:
    if not path.exists():
        return

    def _onerror(func, p, exc_info):
        try:
            Path(p).chmod(0o700)
            func(p)
        except Exception as cleanup_exc:
            logger.warning("Không thể xóa %s: %s", p, cleanup_exc)

    shutil.rmtree(path, ignore_errors=False, onerror=_onerror)


def _can_load_existing_index(
    chroma_dir: Path,
    collection_name: str,
    force_rebuild: bool,
    existing_meta: Dict[str, Any],
    sig: str,
) -> bool:
    if force_rebuild:
        return False
    if existing_meta.get("data_signature") != sig:
        return False
    if not chroma_dir.exists():
        return False

    sqlite_file = chroma_dir / "chroma.sqlite3"
    if not sqlite_file.exists():
        return False

    try:
        db, coll, _, _ = _create_vector_components(chroma_dir, collection_name)
        count = coll.count()
        del coll
        del db
        gc.collect()
        return count > 0
    except Exception as exc:
        logger.warning("Không thể nạp index cũ, sẽ rebuild: %s", exc)
        return False


def _build_new_index(
    profile: TenantProfile,
    chroma_dir: Path,
    collection_name: str,
    meta_file: Path,
    sig: str,
):
    logger.info("Tenant %s: bắt đầu rebuild index...", profile.tenant_id)

    gc.collect()
    _safe_remove_dir(chroma_dir)
    chroma_dir.mkdir(parents=True, exist_ok=True)

    docs = collect_documents(profile.tenant_id)
    if not docs:
        raise RuntimeError("Không có dữ liệu để lập chỉ mục.")

    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes = splitter.get_nodes_from_documents(docs)

    try:
        db, coll, vector_store, storage_context = _create_vector_components(chroma_dir, collection_name)
        index = VectorStoreIndex(nodes, storage_context=storage_context)
        del coll
        del db
    except (sqlite3.OperationalError, chromadb.errors.InternalError) as exc:
        logger.warning("Lỗi khi rebuild ChromaDB, thử dọn DB và rebuild lại 1 lần: %s", exc)
        gc.collect()
        _safe_remove_dir(chroma_dir)
        chroma_dir.mkdir(parents=True, exist_ok=True)
        db, coll, vector_store, storage_context = _create_vector_components(chroma_dir, collection_name)
        index = VectorStoreIndex(nodes, storage_context=storage_context)
        del coll
        del db

    document_count = len(docs)
    node_count = len(nodes)

    meta_payload = {
        "tenant_id": profile.tenant_id,
        "collection_name": collection_name,
        "data_signature": sig,
        "updated_at": now_str(),
        "document_count": document_count,
        "node_count": node_count,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "embed_model": DEFAULT_EMBED_MODEL,
        "top_k": profile.top_k,
        "model_name": profile.model_name,
        "ollama_timeout": OLLAMA_TIMEOUT,
    }
    meta_file.write_text(
        json.dumps(meta_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return index, document_count, node_count


def build_runtime(profile: TenantProfile, force_rebuild: bool = False) -> TenantRuntime:
    start_time = time.time()
    start_ram = get_ram_usage()

    sig = compute_data_signature(profile.tenant_id)
    chroma_dir = tenant_chroma_dir(profile.tenant_id)
    meta_file = tenant_meta_file(profile.tenant_id)
    collection_name = f"tenant_{profile.tenant_id}"

    existing_meta: Dict[str, Any] = {}
    if meta_file.exists():
        try:
            existing_meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Meta file lỗi, bỏ qua: %s", exc)

    should_load_existing = _can_load_existing_index(
        chroma_dir=chroma_dir,
        collection_name=collection_name,
        force_rebuild=force_rebuild,
        existing_meta=existing_meta,
        sig=sig,
    )

    if should_load_existing:
        logger.info("Tenant %s: dữ liệu không đổi, nạp từ ChromaDB.", profile.tenant_id)
        db, coll, vector_store, storage_context = _create_vector_components(chroma_dir, collection_name)
        index = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context,
        )
        document_count = int(existing_meta.get("document_count", 0))
        node_count = int(existing_meta.get("node_count", 0))
        del coll
        del db
    else:
        index, document_count, node_count = _build_new_index(
            profile=profile,
            chroma_dir=chroma_dir,
            collection_name=collection_name,
            meta_file=meta_file,
            sig=sig,
        )

    runtime = TenantRuntime(
        profile=profile,
        index=index,
        retriever=index.as_retriever(similarity_top_k=profile.top_k),
        storage_dir=tenant_storage_dir(profile.tenant_id),
        chroma_dir=chroma_dir,
        collection_name=collection_name,
        data_signature=sig,
        loaded_at=now_str(),
        document_count=document_count,
        node_count=node_count,
    )

    elapsed = time.time() - start_time
    end_ram = get_ram_usage()
    ram_delta = -1.0 if start_ram < 0 or end_ram < 0 else (end_ram - start_ram)

    logger.info(
        "[METRICS] tenant=%s | time=%.2fs | RAM Δ=%s | docs=%s | nodes=%s",
        profile.tenant_id,
        elapsed,
        format_ram_usage(ram_delta),
        document_count,
        node_count,
    )

    RUNTIME_CACHE[profile.tenant_id] = runtime
    return runtime


def get_runtime(profile: TenantProfile) -> TenantRuntime:
    tenant_id = profile.tenant_id

    if tenant_id in RUNTIME_CACHE:
        return RUNTIME_CACHE[tenant_id]

    runtime = build_runtime(profile, force_rebuild=False)
    RUNTIME_CACHE[tenant_id] = runtime
    return runtime