from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from config import AUTO_REFRESH_MINUTES, bootstrap_dirs, ensure_default_config, init_embedding_settings
from llm_service import get_or_create_profile
from workflow import run_workflow
from tools import handle_slash_command
from runtime_manager import build_runtime
from utils import BackgroundScheduler, HAS_PSUTIL, HAS_SCHEDULER, check_ollama_alive

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("system.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

SCHEDULER: Optional[Any] = None


def maybe_start_scheduler(state: Dict[str, Any]) -> None:
    global SCHEDULER

    if AUTO_REFRESH_MINUTES <= 0:
        logger.info("Auto refresh bị tắt vì AUTO_REFRESH_MINUTES <= 0")
        return

    if not HAS_SCHEDULER:
        logger.warning("Không có apscheduler. Bỏ qua auto refresh.")
        return

    if SCHEDULER and getattr(SCHEDULER, "running", False):
        return

    scheduler = BackgroundScheduler()

    def refresh_active_tenant() -> None:
        try:
            tenant_id = state.get("tenant_id", "default")
            profile = get_or_create_profile(tenant_id)
            build_runtime(profile, force_rebuild=False)
            logger.info("Auto refresh hoàn tất cho tenant=%s", tenant_id)
        except Exception as exc:
            logger.error("Auto refresh lỗi: %s", exc)

    scheduler.add_job(refresh_active_tenant, "interval", minutes=AUTO_REFRESH_MINUTES)
    scheduler.start()
    SCHEDULER = scheduler
    logger.info("Scheduler đã bật: mỗi %s phút", AUTO_REFRESH_MINUTES)


def stop_scheduler() -> None:
    global SCHEDULER
    if SCHEDULER and getattr(SCHEDULER, "running", False):
        try:
            SCHEDULER.shutdown(wait=False)
            logger.info("Scheduler đã dừng.")
        except Exception as exc:
            logger.warning("Dừng scheduler lỗi: %s", exc)
    SCHEDULER = None


def main() -> None:
    logger.info("--- KHỞI ĐỘNG AGENTIC RAG 3.2 MODULAR ---")

    bootstrap_dirs()
    ensure_default_config()
    init_embedding_settings()

    if not check_ollama_alive():
        logger.error("Ollama Server chưa bật. Hãy chạy Ollama trước.")
        print("Lỗi: Ollama Server chưa bật. Hãy chạy Ollama trước.")
        return

    tenant_id = os.getenv("TENANT_ID", "default")
    user_id = os.getenv("USER_ID", "guest")

    profile = get_or_create_profile(tenant_id)
    state: Dict[str, Any] = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "show_sources": True,
    }

    try:
        maybe_start_scheduler(state)

        print(f"\n=== SẴN SÀNG (Hệ điều hành: {os.name}) ===")
        print(f"Khách hàng: {profile.display_name} | Người dùng: {user_id}")
        print(f"Scheduler: {'có' if HAS_SCHEDULER else 'không'} | psutil: {'có' if HAS_PSUTIL else 'không'}")

        while True:
            prompt = f"\n[{state['tenant_id']}/{state['user_id']}] Bạn: "
            question = input(prompt).strip()

            if not question:
                continue
            if question.lower() in {"exit", "quit"}:
                break

            if question.startswith("/"):
                profile, state["user_id"], msg = handle_slash_command(
                    question,
                    profile,
                    state["user_id"],
                    state,
                )
                print(f"ChatBot: {msg}")
                continue

            print("AI đang phân tích...", end="\r")
            try:
                answer = run_workflow(
                    profile=profile,
                    user_id=state["user_id"],
                    question=question,
                    show_sources=bool(state.get("show_sources", True)),
                )
                print(f"ChatBot: {answer}")
            except Exception as exc:
                logger.exception("Lỗi khi trả lời")
                print(f"ChatBot: Lỗi hệ thống: {exc}")
    finally:
        stop_scheduler()


if __name__ == "__main__":
    main()