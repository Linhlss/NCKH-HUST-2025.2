from __future__ import annotations

import json
import os
import re
import hashlib
from pathlib import Path
from typing import Any, Dict

from llama_index.core import Settings
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Các module source nằm trong project_root/, nhưng dữ liệu và launcher ở thư mục cha.
SOURCE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = SOURCE_ROOT.parent
DATA_DIR = PROJECT_ROOT / "data"
LEGACY_SHARED_FILES_DIR = DATA_DIR / "files"
LEGACY_SHARED_LINKS_FILE = DATA_DIR / "links.txt"
SHARED_FILES_DIR = DATA_DIR / "shared" / "files"
SHARED_LINKS_FILE = DATA_DIR / "shared" / "links.txt"
TENANTS_DIR = DATA_DIR / "tenants"
STORAGE_ROOT = Path(os.getenv("STORAGE_ROOT_OVERRIDE", str(PROJECT_ROOT / "storage")))
MEMORY_ROOT = PROJECT_ROOT / "memory"
CONFIG_DIR = PROJECT_ROOT / "config"
TENANT_CONFIG_FILE = CONFIG_DIR / "tenants.json"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "system.log"

DEFAULT_MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")
DEFAULT_SHARED_MODEL_NAME = os.getenv("SHARED_OLLAMA_MODEL", DEFAULT_MODEL_NAME)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_EMBED_MODEL = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-base")
ENABLE_WEB_READER = os.getenv("ENABLE_WEB_READER", "true").lower() == "true"
AUTO_REFRESH_MINUTES = int(os.getenv("AUTO_REFRESH_MINUTES", "0"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "700"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "4"))
MAX_SOURCE_NODES = int(os.getenv("MAX_SOURCE_NODES", "5"))
DEFAULT_ENABLE_QUERY_EXPANSION = os.getenv("ENABLE_QUERY_EXPANSION", "false").lower() == "true"
DEFAULT_ENABLE_HYBRID_RETRIEVAL = os.getenv("ENABLE_HYBRID_RETRIEVAL", "false").lower() == "true"
DEFAULT_ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "false").lower() == "true"
DEFAULT_QUERY_EXPANSION_COUNT = int(os.getenv("QUERY_EXPANSION_COUNT", "4"))
DEFAULT_HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.55"))
DEFAULT_RERANKER_TOP_N = int(os.getenv("RERANKER_TOP_N", "8"))
DEFAULT_FIXED_ROUTE_MODE = os.getenv("FIXED_ROUTE_MODE", "adaptive").strip().lower() or "adaptive"
DEFAULT_ENABLE_PERSONALIZATION = os.getenv("ENABLE_PERSONALIZATION", "true").lower() == "true"
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "360"))
OLLAMA_MAX_RETRIES = int(os.getenv("OLLAMA_MAX_RETRIES", "2"))
OLLAMA_RETRY_DELAY = float(os.getenv("OLLAMA_RETRY_DELAY", "1.5"))

# SLA / expected latency
FAST_PATH_SLA_SEC = float(os.getenv("FAST_PATH_SLA_SEC", "5"))
NORMAL_PATH_SLA_SEC = float(os.getenv("NORMAL_PATH_SLA_SEC", "10"))
REBUILD_SLA_SEC = float(os.getenv("REBUILD_SLA_SEC", "30"))

# Cho phép nhận diện file kiểu bảng ở tool path
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".txt", ".md"}

# Những file nên đi tool path thay vì vector-RAG
TABLE_FILE_EXTENSIONS = {".xlsx", ".xls", ".csv"}
TEXT_FILE_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}
_EMBEDDINGS_INITIALIZED = False


class LocalHashEmbedding(BaseEmbedding):
    model_name: str = "local-hash-embedding"
    dim: int = 768

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = re.findall(r"\w+", (text or "").lower())
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            slot = int.from_bytes(digest[:4], "big") % self.dim
            vector[slot] += 1.0
        norm = sum(value * value for value in vector) ** 0.5 or 1.0
        return [value / norm for value in vector]

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._embed(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._embed(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._embed(text)


def bootstrap_dirs() -> None:
    for path in [
        DATA_DIR,
        TENANTS_DIR,
        STORAGE_ROOT,
        MEMORY_ROOT,
        CONFIG_DIR,
        LOG_DIR,
        SHARED_FILES_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def init_embedding_settings() -> None:
    global _EMBEDDINGS_INITIALIZED
    if _EMBEDDINGS_INITIALIZED:
        return
    try:
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=DEFAULT_EMBED_MODEL,
            model_kwargs={"local_files_only": True},
        )
    except Exception:
        Settings.embed_model = LocalHashEmbedding()
    _EMBEDDINGS_INITIALIZED = True


def ensure_default_config() -> None:
    if TENANT_CONFIG_FILE.exists():
        return

    TENANT_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "default": {
            "display_name": "HT Hệ Thống",
            "persona": "Bạn là chuyên gia tư vấn cao cấp.",
            "language_hint": "Tự động",
            "top_k": DEFAULT_TOP_K,
            "memory_turns": 6,
            "model_name": DEFAULT_MODEL_NAME,
            "shared_model_name": DEFAULT_SHARED_MODEL_NAME,
            "adapter_name": "base",
            "enable_personalization": DEFAULT_ENABLE_PERSONALIZATION,
            "fixed_route_mode": DEFAULT_FIXED_ROUTE_MODE,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "enable_query_expansion": DEFAULT_ENABLE_QUERY_EXPANSION,
            "enable_hybrid_retrieval": DEFAULT_ENABLE_HYBRID_RETRIEVAL,
            "enable_reranker": DEFAULT_ENABLE_RERANKER,
            "query_expansion_count": DEFAULT_QUERY_EXPANSION_COUNT,
            "hybrid_alpha": DEFAULT_HYBRID_ALPHA,
            "reranker_top_n": DEFAULT_RERANKER_TOP_N,
        }
    }
    TENANT_CONFIG_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_tenant_configs() -> Dict[str, Dict[str, Any]]:
    ensure_default_config()
    try:
        return json.loads(TENANT_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"default": {}}


def save_tenant_configs(configs: Dict[str, Dict[str, Any]]) -> None:
    TENANT_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    TENANT_CONFIG_FILE.write_text(
        json.dumps(configs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
