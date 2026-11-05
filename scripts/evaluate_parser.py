import argparse
import json
import time
from pathlib import Path

from person_searcher.evaluation.queries import generate_tracking_queries
from person_searcher.query.ollama_parser import OllamaQueryParser
from person_searcher.storage.few_shot import FewShotStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Ollama query parsing.")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--database", type=Path, default=Path("artifacts/search.db"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/parser_results.json"))
    args = parser.parse_args()
    if args.count < 0:
        parser.error("--count must be >= 0")

    examples = FewShotStore(args.database)
    examples.initialize()
    parser_engine = OllamaQueryParser(
        model=args.model, examples=examples
    )
    queries = generate_tracking_queries(args.count, seed=args.seed)
    results = []
    started = time.perf_counter()
    for query in queries:
        try:
            parsed = parser_engine.parse(query)
            results.append({"query": query, "status": "SUCCESS", "parsed": parsed.model_dump()})
        except Exception as exc:
            results.append({"query": query, "status": "FAILED", "error": str(exc)})
    elapsed = time.perf_counter() - started
    success = sum(result["status"] == "SUCCESS" for result in results)
    report = {
        "model": args.model,
        "total": len(results),
        "success": success,
        "failed": len(results) - success,
        "success_rate": success / len(results) if results else 0.0,
        "elapsed_seconds": round(elapsed, 3),
        "details": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"success={success}/{len(results)} ({report['success_rate']:.1%})")
    print(f"report={args.output}")


if __name__ == "__main__":
    main()
