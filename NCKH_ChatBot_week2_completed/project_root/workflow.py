from __future__ import annotations

from memory_store import MemoryStore
from models import TenantProfile
from prompt_builder import (
    append_sources,
    build_general_draft_prompt,
    build_out_of_scope_answer,
    build_query_rewrite_prompt,
    build_rag_draft_prompt,
    build_style_rewrite_prompt,
    build_verification_prompt,
)
from retrieval import retrieve_context
from router import route_question
from runtime_manager import get_runtime
from llm_service import draft_answer, get_llm, rewrite_query, rewrite_style, verify_answer
from utils import normalize_question


def _run_general_chain(profile: TenantProfile, question: str, memory_text: str) -> str:
    llm = get_llm(profile.model_name)
    draft = draft_answer(
        llm,
        build_general_draft_prompt(
            profile=profile,
            question=question,
            memory_text=memory_text,
        ),
    )
    return rewrite_style(
        llm,
        build_style_rewrite_prompt(
            profile=profile,
            question=question,
            answer_text=draft,
            use_internal_context=False,
        ),
    )


def _run_rag_chain(
    profile: TenantProfile,
    question: str,
    memory_text: str,
    show_sources: bool,
) -> str:
    llm = get_llm(profile.model_name)
    rewritten_query = rewrite_query(
        llm,
        build_query_rewrite_prompt(
            profile=profile,
            question=question,
            memory_text=memory_text,
        ),
    )
    runtime = get_runtime(profile)
    retrieved_context, sources = retrieve_context(runtime, question, retrieval_query=rewritten_query)
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
    final_answer = rewrite_style(
        llm,
        build_style_rewrite_prompt(
            profile=profile,
            question=question,
            answer_text=verified,
            use_internal_context=True,
        ),
    )
    return append_sources(final_answer, sources, show_sources)


def run_workflow(
    profile: TenantProfile,
    user_id: str,
    question: str,
    show_sources: bool = True,
) -> str:
    question = normalize_question(question)
    memory = MemoryStore(profile.tenant_id, user_id)
    memory_text = memory.load(profile.memory_turns)
    route_result = route_question(question, profile, user_id)

    if route_result.route == "tool" and route_result.direct_answer:
        answer = route_result.direct_answer
    elif route_result.route == "out_of_scope":
        answer = build_out_of_scope_answer(question)
    elif route_result.route == "general":
        answer = _run_general_chain(profile, question, memory_text)
    else:
        answer = _run_rag_chain(profile, question, memory_text, show_sources)

    memory.append("user", question)
    memory.append("assistant", answer)
    return answer
