from __future__ import annotations

import logging

from project_root.memory_store import MemoryStore
from project_root.models import TenantProfile, WorkflowTrace
from project_root.prompt_builder import (
    append_sources,
    build_general_draft_prompt,
    build_out_of_scope_answer,
    build_query_rewrite_prompt,
    build_rag_draft_prompt,
    build_style_rewrite_prompt,
    build_verification_prompt,
)
from project_root.retrieval import retrieve_context
from project_root.router import route_question
from project_root.runtime_manager import get_runtime
from project_root.llm_service import (
    draft_answer,
    get_llm_for_profile,
    resolve_personalization_state,
    rewrite_query,
    rewrite_style,
    verify_answer,
)
from project_root.utils import normalize_question

logger = logging.getLogger(__name__)


def _run_general_chain(profile: TenantProfile, question: str, memory_text: str) -> str:
    llm = get_llm_for_profile(profile)

    draft = draft_answer(
        llm,
        build_general_draft_prompt(
            profile=profile,
            question=question,
            memory_text=memory_text,
        ),
    )

    final_answer = rewrite_style(
        llm,
        build_style_rewrite_prompt(
            profile=profile,
            question=question,
            answer_text=draft,
            use_internal_context=False,
        ),
    )
    return final_answer


def _run_rag_chain(
    profile: TenantProfile,
    question: str,
    memory_text: str,
    show_sources: bool,
) -> str:
    llm = get_llm_for_profile(profile)

    rewritten_query = rewrite_query(
        llm,
        build_query_rewrite_prompt(
            profile=profile,
            question=question,
            memory_text=memory_text,
        ),
    )

    runtime = get_runtime(profile)
    retrieved_context, sources = retrieve_context(
        runtime,
        question,
        retrieval_query=rewritten_query,
    )

    if not retrieved_context or not retrieved_context.strip():
        return _run_general_chain(profile, question, memory_text)

    draft = draft_answer(
        llm,
        build_rag_draft_prompt(
            profile=profile,
            question=question,
            rewritten_query=rewritten_query,
            memory_text=memory_text,
            retrieved_context=retrieved_context,
        ),
    )

    verified = verify_answer(
        llm,
        build_verification_prompt(
            question=question,
            draft_answer=draft,
            retrieved_context=retrieved_context,
        ),
    )

    if not verified or not verified.strip():
        verified = draft

    final_answer = rewrite_style(
        llm,
        build_style_rewrite_prompt(
            profile=profile,
            question=question,
            answer_text=verified,
            use_internal_context=True,
        ),
    )

    if not final_answer or not final_answer.strip():
        final_answer = verified or draft

    return append_sources(final_answer, sources, show_sources)


def run_workflow_with_trace(
    profile: TenantProfile,
    user_id: str,
    question: str,
    show_sources: bool = True,
) -> tuple[str, WorkflowTrace]:
    question = normalize_question(question)

    memory = MemoryStore(profile.tenant_id, user_id)
    memory_text = memory.load(profile.memory_turns)

    route_result = route_question(question, profile, user_id)
    personalization = resolve_personalization_state(profile)

    if route_result.route == "tool" and route_result.direct_answer:
        answer = route_result.direct_answer

    elif route_result.route == "out_of_scope":
        answer = build_out_of_scope_answer(question)

    elif route_result.route == "general":
        answer = _run_general_chain(profile, question, memory_text)

    elif route_result.route == "retrieval":
        answer = _run_rag_chain(profile, question, memory_text, show_sources)

    else:
        answer = _run_general_chain(profile, question, memory_text)

    trace = WorkflowTrace(
        route=route_result.route,
        route_reason=route_result.reason,
        route_score=route_result.score,
        route_features=route_result.features or {},
        route_candidates=route_result.candidates or {},
        route_mode=profile.fixed_route_mode,
        route_policy=route_result.policy,
        used_adapter=str(personalization["adapter_name"]),
        adapter_enabled=bool(personalization["adapter_enabled"]),
        adapter_available=bool(personalization["adapter_available"]),
        adapter_path=(str(personalization["adapter_path"]) if personalization["adapter_path"] else None),
        shared_model_name=str(personalization["shared_model_name"]),
    )

    logger.info(
        "workflow_trace tenant=%s user=%s route=%s score=%.3f mode=%s policy=%s adapter=%s adapter_available=%s features=%s candidates=%s",
        profile.tenant_id,
        user_id,
        trace.route,
        trace.route_score,
        trace.route_mode,
        trace.route_policy,
        trace.used_adapter,
        trace.adapter_available,
        trace.route_features,
        trace.route_candidates,
    )

    memory.append("user", question)
    memory.append("assistant", answer)

    return answer, trace


def run_workflow(
    profile: TenantProfile,
    user_id: str,
    question: str,
    show_sources: bool = True,
) -> str:
    answer, _ = run_workflow_with_trace(
        profile=profile,
        user_id=user_id,
        question=question,
        show_sources=show_sources,
    )
    return answer
