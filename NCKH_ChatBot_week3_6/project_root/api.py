from __future__ import annotations

import logging
import time
from typing import Optional

from fastapi import FastAPI, HTTPException

from project_root.config import bootstrap_dirs, ensure_default_config, init_embedding_settings, load_tenant_configs
from project_root.llm_service import get_or_create_profile
from project_root.router import route_question
from project_root.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    MemoryResetRequest,
    MessageResponse,
    RefreshRequest,
    SourceItem,
    StatusResponse,
    TenantItem,
    TenantsResponse,
)
from project_root.api_helpers import infer_mode_from_route, parse_sources_from_answer, runtime_status_payload
from project_root.tools import tool_list_tenants
from project_root.workflow import run_workflow
from project_root.memory_store import MemoryStore
from project_root.runtime_manager import build_runtime

app = FastAPI(title="Multi-tenant RAG API", version="v1")
logger = logging.getLogger(__name__)


@app.on_event("startup")
def startup_event() -> None:
    bootstrap_dirs()
    ensure_default_config()
    init_embedding_settings()
    logger.info("FastAPI startup hoàn tất: đã bootstrap thư mục và khởi tạo embedding settings.")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="multi-tenant-rag", version="v1")


@app.get("/tenants", response_model=TenantsResponse)
def list_tenants() -> TenantsResponse:
    configs = load_tenant_configs()
    items = []
    for tenant_id, raw in configs.items():
        items.append(
            TenantItem(
                tenant_id=tenant_id,
                display_name=raw.get("display_name", tenant_id),
                language_hint=raw.get("language_hint", "Tự động"),
                has_adapter=(raw.get("adapter_name", "base") != "base"),
            )
        )
    return TenantsResponse(tenants=items)


@app.post("/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def chat(req: ChatRequest) -> ChatResponse:
    started = time.perf_counter()
    try:
        profile = get_or_create_profile(req.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail={"status": "error", "error_code": "TENANT_NOT_FOUND", "message": str(exc)})

    try:
        route_result = route_question(req.message, profile, req.user_id)
        answer = run_workflow(
            profile=profile,
            user_id=req.user_id,
            question=req.message,
            show_sources=req.show_sources,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        sources = parse_sources_from_answer(answer)
        return ChatResponse(
            status="ok",
            answer=answer,
            route=route_result.route,
            mode=infer_mode_from_route(route_result.route),
            tenant_id=req.tenant_id,
            user_id=req.user_id,
            sources=sources,
            metadata={
                "latency_ms": latency_ms,
                "used_adapter": profile.adapter_name,
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": str(exc),
            },
        )


@app.post("/memory/reset", response_model=MessageResponse, responses={500: {"model": ErrorResponse}})
def memory_reset(req: MemoryResetRequest) -> MessageResponse:
    try:
        MemoryStore(req.tenant_id, req.user_id).reset()
        return MessageResponse(status="ok", message="Đã xóa sạch bộ nhớ hội thoại.")
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": str(exc),
            },
        )


@app.get("/status", response_model=StatusResponse, responses={500: {"model": ErrorResponse}})
def status(tenant_id: str = "default", user_id: str = "guest") -> StatusResponse:
    try:
        profile = get_or_create_profile(tenant_id)
        payload = runtime_status_payload(profile, user_id)
        return StatusResponse(**payload)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": str(exc),
            },
        )


@app.post("/refresh", response_model=MessageResponse, responses={500: {"model": ErrorResponse}})
def refresh(req: RefreshRequest) -> MessageResponse:
    try:
        profile = get_or_create_profile(req.tenant_id)
        build_runtime(profile, force_rebuild=True)
        return MessageResponse(status="ok", message="Đã làm mới dữ liệu.")
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_code": "RUNTIME_BUILD_FAILED",
                "message": str(exc),
            },
        )
