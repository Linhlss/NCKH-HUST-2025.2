from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from evaluation.evaluate_answers import evaluate_predictions as evaluate_answer_predictions
from evaluation.evaluate_answers import render_markdown as render_answer_markdown
from evaluation.evaluate_retrieval import evaluate_variant, load_cases, render_error_analysis, render_report

def _read_predictions(path: str | Path) -> List[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="evaluation/test_queries.json")
    parser.add_argument("--variant", default="dense_prioritized", choices=["dense_raw", "dense_prioritized"])
    parser.add_argument("--label", required=True)
    parser.add_argument("--answer-predictions", default="")
    parser.add_argument("--output-dir", default="evaluation/generated_reports")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cases = load_cases(Path(args.dataset))
    retrieval_report = evaluate_variant(cases, args.variant)

    (output_dir / f"{args.label}_retrieval_report.json").write_text(
        json.dumps(retrieval_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / f"{args.label}_retrieval_report.md").write_text(
        render_report([retrieval_report]),
        encoding="utf-8",
    )
    (output_dir / f"{args.label}_error_analysis.md").write_text(
        render_error_analysis([retrieval_report]),
        encoding="utf-8",
    )

    if args.answer_predictions:
        answer_predictions = _read_predictions(args.answer_predictions)
        answer_report = evaluate_answer_predictions(cases, answer_predictions)
        (output_dir / f"{args.label}_answer_report.json").write_text(
            json.dumps(answer_report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_dir / f"{args.label}_answer_report.md").write_text(
            render_answer_markdown(answer_report, args.label),
            encoding="utf-8",
        )

if __name__ == "__main__":
    main()
