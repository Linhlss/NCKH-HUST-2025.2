from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from llama_index.core import Settings
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
STORAGE_ROOT = PROJECT_ROOT / "storage"
MEMORY_ROOT = PROJECT_ROOT / "memory"
CONFIG_DIR = PROJECT_ROOT / "config"
TENANT_CONFIG_FILE = CONFIG_DIR / "tenants.json"
LOG_FILE = PROJECT_ROOT / "system.log"

DEFAULT_MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")
DEFAULT_EMBED_MODEL = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-base")
ENABLE_WEB_READER = os.getenv("ENABLE_WEB_READER", "true").lower() == "true"
AUTO_REFRESH_MINUTES = int(os.getenv("AUTO_REFRESH_MINUTES", "0"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "700"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "4"))
MAX_SOURCE_NODES = int(os.getenv("MAX_SOURCE_NODES", "5"))
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


def bootstrap_dirs() -> None:
    for path in [
        DATA_DIR,
        TENANTS_DIR,
        STORAGE_ROOT,
        MEMORY_ROOT,
        CONFIG_DIR,
        SHARED_FILES_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def init_embedding_settings() -> None:
    Settings.embed_model = HuggingFaceEmbedding(model_name=DEFAULT_EMBED_MODEL)


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
            "adapter_name": "base",
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