# 11.5 변경 사항
기존 스크립트는 해당 브랜치로 보존하며, 통합된 개발 환경은 `src/person_searcher` 내부를 기준으로 시작

## 1. 환경 설정 및 설치

Python 버전 3.10 이상

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install -e ".[dev,ollama]"
```

## 2. Annotation 크롭 생성
--annotations: [라벨] 디렉터리가 포함된 경로

--images: [원천] 디렉터리가 포함된 경로
(두 경로 모두 공통 데이터셋 경로로 지정)


```PowerShell
# 전체 데이터셋 처리
python scripts\ingest_annotations.py `
  --annotations "data\지하철 역사 내 CCTV 이상행동 영상\Training" `
  --images "data\지하철 역사 내 CCTV 이상행동 영상\Training"

# 소량 데이터 검증용
python scripts\ingest_annotations.py `
  --annotations "data\지하철 역사 내 CCTV 이상행동 영상\Training" `
  --images "data\지하철 역사 내 CCTV 이상행동 영상\Training" `
  --limit 10 `
  --batch-size 3
```

```Bash
PYTHONPATH=src python scripts/ingest_annotations.py \
  --annotations "data/지하철 역사 내 CCTV 이상행동 영상/Training" \
  --images "data/지하철 역사 내 CCTV 이상행동 영상/Training" \
  --limit 10 \
  --batch-size 3
```

* 기본적으로 artifacts/crops와 artifacts/search.db에 저장
* 현재 구현 단계: Annotation의 바운딩 박스를 직접 활용 중이며, 향후 크롭 파이프라인 이후에 YOLO 검출 및 의류 속성 추출 모듈을 별도로 연동할 예정

## 3. 자연어 Parser 실행 및 평가
### 3-1. Ollama 설치 및 모델 준비
```Bash
pip install ollama
ollama pull qwen2.5:7b
```
### 3-2. 대화형 파서 실행
```Bash
PYTHONPATH=src python scripts/interactive_parser.py --model qwen2.5:7b
```
### 3-3. 파서 배치 평가
```Bash
PYTHONPATH=src python scripts/evaluate_parser.py \
  --count 10 \
  --seed 42 \
  --model qwen2.5:7b
```
* 평가에서는 프로토타입과 마찬가지로 JSON/Pydantic 파싱 성공률을 측정
* 의미 정확도 및 이미지 검색 정확도는 향후 정답(=Ground Truth) 데이터셋이 추가된 뒤 별도로 평가될 예정