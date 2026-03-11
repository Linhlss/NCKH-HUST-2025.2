from __future__ import annotations

import json
import logging
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional

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

    db = chromadb.PersistentClient(path=str(chroma_dir))
    coll = db.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=coll)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    should_load_existing = (
        not force_rebuild
        and existing_meta.get("data_signature") == sig
        and coll.count() > 0
    )

    if should_load_existing:
        logger.info("Tenant %s: dữ liệu không đổi, nạp từ ChromaDB.", profile.tenant_id)
        index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)
        document_count = int(existing_meta.get("document_count", 0))
        node_count = int(existing_meta.get("node_count", 0))
    else:
        logger.info("Tenant %s: bắt đầu rebuild index...", profile.tenant_id)

        shutil.rmtree(chroma_dir, ignore_errors=True)
        chroma_dir.mkdir(parents=True, exist_ok=True)

        db = chromadb.PersistentClient(path=str(chroma_dir))
        coll = db.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=coll)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        docs = collect_documents(profile.tenant_id)
        if not docs:
            raise RuntimeError("Không có dữ liệu để lập chỉ mục.")

        splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        nodes = splitter.get_nodes_from_documents(docs)
        index = VectorStoreIndex(nodes, storage_context=storage_context)
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
    return RUNTIME_CACHE.get(profile.tenant_id) or build_runtime(profile)