from __future__ import annotations

import argparse
from dataclasses import replace
import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from project_root.api_helpers import parse_sources_from_answer
from project_root.config import bootstrap_dirs, ensure_default_config, init_embedding_settings
from project_root.llm_service import get_or_create_profile
from project_root.router import route_question
from project_root.utils import check_ollama_alive
from project_root.workflow import run_workflow_with_trace

from evaluation.evaluate_answers import evaluate_predictions as evaluate_answer_predictions
from evaluation.evaluate_answers import render_markdown as render_answer_markdown
from evaluation.evaluate_retrieval import load_cases

def _source_item_to_name(item) -> str:
    if hasattr(item, "name"):
        return str(item.name)
    if isinstance(item, dict):
        return str(item.get("name") or item.get("source") or "")
    return str(item)

def run_predictions(dataset_path: Path, fixed_route_mode: str | None = None) -> list[dict]:
    bootstrap_dirs()
    ensure_default_config()
    init_embedding_settings()

    cases = load_cases(dataset_path)
    predictions = []
    for index, case in enumerate(cases, start=1):
        profile = get_or_create_profile(case.tenant_id)
        if fixed_route_mode:
            profile = replace(profile, fixed_route_mode=fixed_route_mode)
        route = route_question(case.query, profile, "eval")
        started = time.perf_counter()
        answer, trace = run_workflow_with_trace(
            profile=profile,
            user_id="eval_user",
            question=case.query,
            show_sources=True,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        sources = parse_sources_from_answer(answer)

        predictions.append({
            "id": case.id,
            "tenant_id": case.tenant_id,
            "query": case.query,
            "route": route.route,
            "answer": answer,
            "sources": [_source_item_to_name(item) for item in sources],
            "latency_ms": latency_ms,
            "route_reason": trace.route_reason,
            "route_score": trace.route_score,
            "route_mode": trace.route_mode,
            "route_policy": trace.route_policy,
            "used_adapter": trace.used_adapter,
            "adapter_available": trace.adapter_available,
        })
        print(f"[{index}/{len(cases)}] {case.id} route={route.route} latency={latency_ms}ms")
    return predictions

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="evaluation/test_queries.json")
    parser.add_argument("--label", default="baseline_real")
    parser.add_argument("--output-dir", default="evaluation/generated_reports")
    parser.add_argument("--fixed-route-mode", choices=["adaptive", "tool", "retrieval", "general", "out_of_scope"], default=None)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = Path(args.dataset)

    if not check_ollama_alive():
        print("Ollama is not reachable on 127.0.0.1:11434", file=sys.stderr)
        return 2

    predictions = run_predictions(dataset_path, fixed_route_mode=args.fixed_route_mode)
    pred_path = output_dir / f"{args.label}_predictions.json"
    pred_path.write_text(json.dumps(predictions, ensure_ascii=False, indent=2), encoding="utf-8")

    cases = load_cases(dataset_path)
    answer_report = evaluate_answer_predictions(cases, predictions)

    (output_dir / f"{args.label}_answer_report.json").write_text(
        json.dumps(answer_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / f"{args.label}_answer_report.md").write_text(
        render_answer_markdown(answer_report, args.label),
        encoding="utf-8",
    )

    print(f"Saved predictions to {pred_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
