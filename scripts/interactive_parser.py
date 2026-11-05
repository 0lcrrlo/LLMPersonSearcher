import argparse
import json
from pathlib import Path

from person_searcher.query.builder import build_mongo_query
from person_searcher.query.ollama_parser import OllamaQueryParser
from person_searcher.storage.few_shot import FewShotStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactively parse search queries.")
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--database", type=Path, default=Path("artifacts/search.db"))
    args = parser.parse_args()

    examples = FewShotStore(args.database)
    examples.initialize()
    parser_engine = OllamaQueryParser(model=args.model, examples=examples)
    print("종료하려면 q, exit 또는 종료를 입력하세요.")
    while True:
        query = input("검색어> ").strip()
        if query.lower() in {"q", "exit", "quit", "종료"}:
            return
        if not query:
            continue
        condition = parser_engine.parse(query)
        print(json.dumps(condition.model_dump(), ensure_ascii=False, indent=2))
        print(json.dumps(build_mongo_query(condition), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
