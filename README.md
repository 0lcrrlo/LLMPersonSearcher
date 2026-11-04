# LLMPersonSearcher

현재 저장소의 기존 한국어 스크립트는 LLM 파싱 프로토타입으로 보존하고,
새 구현은 `src/person_searcher`에서 시작합니다.

## 현재 구현 범위

- 공통 Pydantic 검색 조건 모델
- 한국어/영어 taxonomy 정규화
- Ollama 구조화 출력 parser
- 배열 요소가 섞이지 않는 MongoDB `$elemMatch` query builder
- 기존 annotation JSON에서 사람/아이 bounding box를 읽는 ingestion
- 원본 frame crop 저장 및 SQLite detection metadata 저장

## 설치

Python 3.10 이상을 사용합니다.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ollama]"
```

## Annotation crop 생성

`--annotations`는 `[라벨]...` 디렉터리, `--images`는 `[원천]...` 디렉터리를
포함하는 공통 데이터셋 경로를 지정합니다.

```powershell
python scripts\ingest_annotations.py `
  --annotations "data\지하철 역사 내 CCTV 이상행동 영상\Training" `
  --images "data\지하철 역사 내 CCTV 이상행동 영상\Training"
```

처음에는 `--limit`으로 소량만 검증할 수 있습니다.

```powershell
python scripts\ingest_annotations.py `
  --annotations "data\지하철 역사 내 CCTV 이상행동 영상\Training" `
  --images "data\지하철 역사 내 CCTV 이상행동 영상\Training" `
  --limit 10 `
  --batch-size 3
```

Git Bash에서는 PowerShell의 백틱(`)이 줄 연결 문자가 아니므로 `\`를
사용하고, 경로 구분자는 `/`로 작성합니다.

```bash
PYTHONPATH=src python scripts/ingest_annotations.py \
  --annotations "data/지하철 역사 내 CCTV 이상행동 영상/Training" \
  --images "data/지하철 역사 내 CCTV 이상행동 영상/Training" \
  --limit 10 \
  --batch-size 3
```

실행 결과는 기본적으로 `artifacts\crops`와 `artifacts\search.db`에 저장됩니다.
전체 데이터는 시간이 오래 걸릴 수 있으므로 먼저 제한된 건수로 확인하세요.

현재 단계에서는 annotation의 bounding box를 사용합니다. YOLO 검출과 의류
속성 추출은 crop pipeline 이후 별도 모듈로 연결할 예정입니다.