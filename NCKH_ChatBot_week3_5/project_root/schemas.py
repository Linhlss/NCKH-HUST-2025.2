from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


class TenantItem(BaseModel):
    tenant_id: str
    display_name: str
    language_hint: str
    has_adapter: bool = False


class TenantsResponse(BaseModel):
    tenants: List[TenantItem]


class ChatRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    show_sources: bool = True


class SourceItem(BaseModel):
    type: str
    name: str
    scope: str
    page_label: Optional[str] = None
    score: Optional[float] = None


class ChatResponse(BaseModel):
    status: Literal["ok"]
    answer: str
    route: Literal["tool", "retrieval", "general", "out_of_scope"]
    mode: Literal["fast_path", "normal_path", "slow_path"]
    tenant_id: str
    user_id: str
    sources: List[SourceItem] = []
    metadata: Dict[str, Any] = {}


class MemoryResetRequest(BaseModel):
    tenant_id: str
    user_id: str


class RefreshRequest(BaseModel):
    tenant_id: str


class MessageResponse(BaseModel):
    status: Literal["ok"]
    message: str


class StatusRuntime(BaseModel):
    docs: Any
    nodes: Any
    loaded_at: Any


class StatusResources(BaseModel):
    ram: str


class StatusModel(BaseModel):
    name: str
    adapter: str


class StatusResponse(BaseModel):
    status: Literal["ok"]
    tenant_id: str
    user_id: str
    runtime: StatusRuntime
    resources: StatusResources
    model: StatusModel


class ErrorResponse(BaseModel):
    status: Literal["error"]
    error_code: str
    message: str
