from project_root.workflow import run_workflow
from project_root.llm_service import generate_answer
from project_root.prompt_builder import build_prompt
from project_root.verifier import verify_answer
from project_root.rewriter import rewrite_answer
from project_root.tools import tool_router
from project_root.memory_store import MemoryStore


memory = MemoryStore()


def run_pipeline3(query: str):

    # ======================
    # 1. TOOL
    # ======================
    tool_result = tool_router(query)
    if tool_result:
        return tool_result

    # ======================
    # 2. WORKFLOW
    # ======================
    result = run_workflow(query)
    docs = result.get("docs", [])

    # ======================
    # 3. MEMORY
    # ======================
    history = memory.get_last_k(3)

    # ======================
    # 4. PROMPT
    # ======================
    prompt = build_prompt(query, docs, history)

    # ======================
    # 5. LLM
    # ======================
    answer = generate_answer(prompt)

    # ======================
    # 6. VERIFY
    # ======================
    if not verify_answer(answer, docs):
        return "❌ Không tìm thấy thông tin phù hợp."

    # ======================
    # 7. REWRITE
    # ======================
    final_answer = rewrite_answer(answer, docs)

    # ======================
    # 8. SAVE MEMORY
    # ======================
    memory.add(query, final_answer)

    return final_answer