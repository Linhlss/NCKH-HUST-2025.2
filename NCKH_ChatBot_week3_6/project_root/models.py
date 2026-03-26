from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from project_root.config import DEFAULT_MODEL_NAME, DEFAULT_TOP_K


@dataclass
class TenantProfile:
    tenant_id: str
    display_name: str
    persona: str
    language_hint: str = "Tự động theo ngôn ngữ câu hỏi"
    top_k: int = DEFAULT_TOP_K
    memory_turns: int = 6
    model_name: str = DEFAULT_MODEL_NAME
    adapter_name: str = "base"


@dataclass
class TenantRuntime:
    profile: TenantProfile
    index: Any
    retriever: Any
    storage_dir: Path
    chroma_dir: Path
    collection_name: str
    data_signature: str
    loaded_at: str
    document_count: int
    node_count: int
