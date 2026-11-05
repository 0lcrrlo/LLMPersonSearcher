# 11.5. 변경사항
기존 script는 해당 브랜치로 보존하고, 통합된 환경을 src/person_Searcher 내에서 시작.

## 설치
Python 3.10 이상

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ollama]"
```

## Annotation 크롭 생성
`--annotations`는 `[라벨]...` 디렉터리, `--images`는 `[원천]...` 디렉터리를
포함하는 공통 데이터셋 경로를 지정함.

```powershell
python scripts\ingest_annotations.py `
  --annotations "data\지하철 역사 내 CCTV 이상행동 영상\Training" `
  --images "data\지하철 역사 내 CCTV 이상행동 영상\Training"
```

`--limit`으로 소량만 검증

```powershell
python scripts\ingest_annotations.py `
  --annotations "data\지하철 역사 내 CCTV 이상행동 영상\Training" `
  --images "data\지하철 역사 내 CCTV 이상행동 영상\Training" `
  --limit 10 `
  --batch-size 3
```

if) git bash에서는 PowerShell의 백틱(`)이 줄 연결 문자가 아니므로 `\`를
사용하고, 경로 구분자는 `/`로 작성

```bash
PYTHONPATH=src python scripts/ingest_annotations.py \
  --annotations "data/지하철 역사 내 CCTV 이상행동 영상/Training" \
  --images "data/지하철 역사 내 CCTV 이상행동 영상/Training" \
  --limit 10 \
  --batch-size 3
```

실행 결과는 기본적으로 `artifacts\crops`와 `artifacts\search.db`에 저장.

현재 단계에서는 annotation의 bounding box를 사용합니다. YOLO 검출과 의류
속성 추출은 crop pipeline 이후 별도 모듈로 연결할 예정

## 자연어 parser 실행

Ollama 설치

```bash
ollama pull qwen2.5:7b
PYTHONPATH=src python scripts/interactive_parser.py --model qwen2.5:7b
```

파서 배치 평가

```bash
PYTHONPATH=src python scripts/evaluate_parser.py \
  --count 10 \
  --seed 42 \
  --model qwen2.5:7b
```

이 평가는 prototype과 마찬가지로 JSON/Pydantic 파싱 성공률을 측정함.
의미 정확도와 이미지 검색 정확도는 정답 데이터셋이 추가된 뒤 별도 평가할 예정.