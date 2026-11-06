# LLMPersonSearcher

## YOLO 인물 탐지

YOLO는 현재 환경에 자동으로 포함되지 않는 선택 의존성입니다. 설치하면
Ultralytics가 모델 가중치(`yolo11n.pt`)를 처음 실행할 때 다운로드합니다.

```bash
python -m pip install -e ".[yolo]"
```

annotation이 없는 이벤트 입력 frame에서 인물 탐지와 crop 저장을 실행합니다.
`--limit`은 frame 수 제한이며, 먼저 소량으로 모델과 경로를 확인하세요.

```bash
PYTHONPATH=src python scripts/ingest_yolo.py \
  --images "data/지하철 역사 내 CCTV 이상행동 영상/Training" \
  --event-class "개집표기 무단진입" \
  --split inference \
  --limit 10 \
  --confidence 0.25
```

탐지 결과는 annotation ingestion과 동일하게 `artifacts/search.db`의
`person_detection`에 저장되고, crop은 `artifacts/crops`에 저장됩니다.
YOLO 탐지에는 `global_id`가 없으므로 실행별 synthetic ID를 사용합니다.
동일 frame을 다시 넣을 때는 기존 unique index에 의해 중복이 무시됩니다.

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

## Person attribute schema

LLM/parser 또는 vision attribute extractor의 조건은 다음 canonical field로
정규화됩니다.

```text
category: upper_body | lower_body | outerwear | bag | ...
color: blue | black | ...
item_type: t_shirt | jeans | ...
```

`person_detection`이 사람 crop의 위치/이벤트 메타데이터를 보관하고,
`person_attribute`가 detection별 의류/액세서리 속성을 보관합니다.
`colors`처럼 한 조건에 여러 색상이 있으면 DB에는 색상별 행으로 저장해
각 필드를 인덱싱할 수 있도록 했습니다.