from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Sequence

from evaluation.evaluate_retrieval import QueryCase, load_cases


def _safe_mean(values: Iterable[float]) -> float:
    values = list(values)
    return mean(values) if values else 0.0


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _normalize_source_name(value: str) -> str:
    return Path(str(value).strip()).name.lower()


def _extract_sources(raw_pred: Dict[str, Any]) -> List[str]:
    raw_sources = raw_pred.get("sources") or raw_pred.get("results") or []
    normalized: List[str] = []
    for item in raw_sources:
        if isinstance(item, str):
            normalized.append(_normalize_source_name(item))
        elif isinstance(item, dict):
            value = item.get("name") or item.get("source") or item.get("file_name") or item.get("path") or ""
            if value:
                normalized.append(_normalize_source_name(value))
    return normalized


def _keyword_coverage(answer: str, expected_keywords: Sequence[str]) -> float:
    if not expected_keywords:
        return 0.0
    lowered = answer.lower()
    hits = sum(1 for keyword in expected_keywords if keyword.lower() in lowered)
    return hits / len(expected_keywords)


def _context_groundedness(answer: str, raw_pred: Dict[str, Any], case: QueryCase) -> float:
    context_chunks: List[str] = []
    for key in ("contexts", "source_texts"):
        value = raw_pred.get(key) or []
        if isinstance(value, list):
            context_chunks.extend(str(item) for item in value)
    for key in ("context", "retrieved_context"):
        value = raw_pred.get(key)
        if isinstance(value, str):
            context_chunks.append(value)

    context_text = " ".join(context_chunks).strip()
    if context_text:
        answer_tokens = {tok for tok in _tokenize(answer) if len(tok) > 2}
        if not answer_tokens:
            return 0.0
        return len(answer_tokens & _tokenize(context_text)) / len(answer_tokens)

    source_docs = set(_extract_sources(raw_pred))
    relevant_docs = {_normalize_source_name(doc) for doc in case.relevant_sources}
    source_hit = 1.0 if source_docs & relevant_docs else 0.0
    return min(1.0, 0.7 * _keyword_coverage(answer, case.expected_answer_keywords) + 0.3 * source_hit)


def _prediction_map(raw_predictions: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for item in raw_predictions:
        key = str(item.get("id") or item.get("query") or "").strip()
        if key:
            mapping[key] = item
    return mapping


def evaluate_predictions(cases: Sequence[QueryCase], predictions: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    pred_map = _prediction_map(predictions)
    rows: List[Dict[str, Any]] = []

    for case in cases:
        raw_pred = pred_map.get(case.id) or pred_map.get(case.query) or {}
        answer = str(raw_pred.get("answer") or "")
        route_match = float(case.expected_route == raw_pred.get("route")) if case.expected_route else 0.5
        keyword_coverage = _keyword_coverage(answer, case.expected_answer_keywords)
        completeness = keyword_coverage
        groundedness = _context_groundedness(answer, raw_pred, case)
        accuracy = min(1.0, 0.75 * keyword_coverage + 0.25 * route_match)
        hallucination_rate = max(0.0, 1.0 - groundedness)

        rows.append(
            {
                "id": case.id,
                "tenant_id": case.tenant_id,
                "category": case.category,
                "difficulty": case.difficulty,
                "query": case.query,
                "accuracy": accuracy,
                "groundedness": groundedness,
                "hallucination_rate": hallucination_rate,
                "completeness": completeness,
                "route_match": route_match,
                "answer": answer,
            }
        )

    overall = {
        metric: _safe_mean(row[metric] for row in rows)
        for metric in ("accuracy", "groundedness", "hallucination_rate", "completeness", "route_match")
    }

    by_slice: Dict[str, Dict[str, Any]] = {}
    for field in ("tenant_id", "category", "difficulty"):
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row[field])].append(row)
        by_slice[field] = {
            name: {
                "count": len(group_rows),
                **{
                    metric: _safe_mean(row[metric] for row in group_rows)
                    for metric in ("accuracy", "groundedness", "hallucination_rate", "completeness", "route_match")
                },
            }
            for name, group_rows in sorted(grouped.items())
        }

    weakest = sorted(rows, key=lambda row: (row["accuracy"], row["groundedness"], row["completeness"]))[:10]
    return {"overall": overall, "by_slice": by_slice, "weakest": weakest, "rows": rows}


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header_line, sep_line, *body])


def render_markdown(report: Dict[str, Any], label: str) -> str:
    overall = report["overall"]
    category_rows = [
        [name, metrics["count"], f"{metrics['accuracy']:.3f}", f"{metrics['groundedness']:.3f}", f"{metrics['hallucination_rate']:.3f}", f"{metrics['completeness']:.3f}"]
        for name, metrics in report["by_slice"]["category"].items()
    ]
    weakest_rows = [
        [item["id"], item["category"], item["difficulty"], f"{item['accuracy']:.3f}", f"{item['groundedness']:.3f}", item["query"]]
        for item in report["weakest"]
    ] or [["-", "-", "-", "-", "-", "Không có mẫu đánh giá"]]

    return "\n".join(
        [
            f"# Answer-Level Evaluation Report - {label}",
            "",
            "## Overall Metrics",
            _table(
                ["System", "Accuracy", "Groundedness", "Hallucination Rate", "Completeness", "Route Match"],
                [[label, f"{overall['accuracy']:.3f}", f"{overall['groundedness']:.3f}", f"{overall['hallucination_rate']:.3f}", f"{overall['completeness']:.3f}", f"{overall['route_match']:.3f}"]],
            ),
            "",
            "## Metrics by Category",
            _table(["Category", "Count", "Accuracy", "Groundedness", "Hallucination", "Completeness"], category_rows),
            "",
            "## Weak Samples",
            _table(["ID", "Category", "Difficulty", "Accuracy", "Groundedness", "Query"], weakest_rows),
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate answer-level predictions with lightweight lexical metrics.")
    parser.add_argument("--dataset", default="evaluation/test_queries.json")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--label", default="baseline")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    cases = load_cases(Path(args.dataset))
    predictions = json.loads(Path(args.predictions).read_text(encoding="utf-8"))
    report = evaluate_predictions(cases, predictions)
    rendered = render_markdown(report, args.label)
    print(rendered)

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.output_md:
        Path(args.output_md).write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
