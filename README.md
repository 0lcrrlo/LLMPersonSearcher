# LLMPersonSearcher

## 저장된 인물 detection 조회

먼저 annotation ingestion으로 SQLite DB를 생성합니다.

```bash
PYTHONPATH=src python scripts/ingest_annotations.py \
  --annotations "data/지하철 역사 내 CCTV 이상행동 영상/Training" \
  --images "data/지하철 역사 내 CCTV 이상행동 영상/Training" \
  --event-class "개집표기 무단진입" \
  --limit 10 \
  --batch-size 3
```

그 다음 CLI로 저장된 인물을 조회합니다.

```bash
PYTHONPATH=src python scripts/query_detections.py \
  --database artifacts/search.db \
  --event-class "개집표기 무단진입" \
  --category person \
  --limit 20
```

사용 가능한 필터는 `--event-class`, `--split`, `--video-id`,
`--global-id`, `--category`, `--limit`입니다.