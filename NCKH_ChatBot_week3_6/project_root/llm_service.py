from __future__ import annotations

import logging
import time
from typing import Dict, Optional

from llama_index.llms.ollama import Ollama

from project_root.config import (
    DEFAULT_MODEL_NAME,
    DEFAULT_TOP_K,
    OLLAMA_MAX_RETRIES,
    OLLAMA_RETRY_DELAY,
    OLLAMA_TIMEOUT,
    load_tenant_configs,
    save_tenant_configs,
)
from project_root.models import TenantProfile
from project_root.utils import sanitize_id

logger = logging.getLogger(__name__)

LLM_CACHE: Dict[str, Ollama] = {}


def get_or_create_profile(tenant_id: str) -> TenantProfile:
    tenant_id = sanitize_id(tenant_id, "default")
    configs = load_tenant_configs()

    if tenant_id not in configs:
        configs[tenant_id] = configs.get("default", {}).copy()
        configs[tenant_id]["display_name"] = tenant_id.replace("_", " ").title()
        save_tenant_configs(configs)

    raw = configs[tenant_id]
    return TenantProfile(
        tenant_id=tenant_id,
        display_name=raw.get("display_name", tenant_id),
        persona=raw.get("persona", ""),
        language_hint=raw.get("language_hint", "Tự động"),
        top_k=int(raw.get("top_k", DEFAULT_TOP_K)),
        memory_turns=int(raw.get("memory_turns", 6)),
        model_name=raw.get("model_name", DEFAULT_MODEL_NAME),
        adapter_name=raw.get("adapter_name", "base"),
    )


def get_llm(model_name: str) -> Ollama:
    if model_name not in LLM_CACHE:
        LLM_CACHE[model_name] = Ollama(
            model=model_name,
            request_timeout=OLLAMA_TIMEOUT,
        )
    return LLM_CACHE[model_name]


def complete_with_retry(llm: Ollama, prompt: str) -> str:
    last_error: Optional[Exception] = None

    for attempt in range(OLLAMA_MAX_RETRIES + 1):
        try:
            response = llm.complete(prompt)
            return str(response.text).strip()
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Ollama call lỗi (attempt %s/%s): %s",
                attempt + 1,
                OLLAMA_MAX_RETRIES + 1,
                exc,
            )
            if attempt < OLLAMA_MAX_RETRIES:
                time.sleep(OLLAMA_RETRY_DELAY)

    raise RuntimeError(f"Ollama thất bại sau nhiều lần thử: {last_error}")


def draft_answer(llm: Ollama, prompt: str) -> str:
    return complete_with_retry(llm, prompt)


def rewrite_query(llm: Ollama, prompt: str) -> str:
    return complete_with_retry(llm, prompt)


def verify_answer(llm: Ollama, prompt: str) -> str:
    return complete_with_retry(llm, prompt)


def rewrite_style(llm: Ollama, prompt: str) -> str:
    return complete_with_retry(llm, prompt)
