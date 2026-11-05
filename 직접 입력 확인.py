import json
from typing import List
from pydantic import BaseModel, Field
import ollama

# ==========================================
# 1. Pydantic 스키마 정의
# ==========================================
class ItemCondition(BaseModel):
    category: str = Field(description="항목의 대분류 (상의, 하의, 아우터, 가방, 신발, 모자 등)")
    color: List[str] = Field(description="추출된 색상 목록")
    type: str = Field(description="상세 종류")

class PersonSearchCondition(BaseModel):
    clothing: List[ItemCondition] = Field(default_factory=list, description="착용한 의류 정보")
    accessories: List[ItemCondition] = Field(default_factory=list, description="소지품 및 악세서리 정보")

# ==========================================
# 2. MongoDB 쿼리 자동 변환 함수
# ==========================================
def convert_to_mongodb_query(parsed_json: dict) -> dict:
    """추출된 JSON 데이터를 DB에서 즉시 실행 가능한 MongoDB $and/$in 쿼리로 변환합니다."""
    and_clauses = []
    
    for item in parsed_json.get("clothing", []):
        item_filters = []
        if item.get("category"):
            item_filters.append({"clothing.category": item["category"]})
        if item.get("color"):
            item_filters.append({"clothing.color": {"$in": item["color"]}})
        if item.get("type"):
            item_filters.append({"clothing.type": item["type"]})
        if item_filters:
            and_clauses.append({"$and": item_filters})
            
    for item in parsed_json.get("accessories", []):
        item_filters = []
        if item.get("category"):
            item_filters.append({"accessories.category": item["category"]})
        if item.get("color"):
            item_filters.append({"accessories.color": {"$in": item["color"]}})
        if item.get("type"):
            item_filters.append({"accessories.type": item["type"]})
        if item_filters:
            and_clauses.append({"$and": item_filters})
            
    return {"$and": and_clauses} if and_clauses else {}

# ==========================================
# 3. 대화형 파싱 테스트 루프
# ==========================================
def run_interactive_parser(model_name="qwen2.5:7b"):
    system_instruction = """
    당신은 지능형 CCTV 검색 질의 분석기입니다.
    사용자의 자연어 묘사에서 '의류'와 '소지품'을 구분하고, 각각의 '색상'과 '종류'를 정확히 분리하여 추출하세요.
    - 색상은 항상 리스트 형태로 반환하세요 (예: "파란" -> ["파란색"]).
    - '어두운' -> ["검은색", "남색", "회색"], '밝은' -> ["흰색", "아이보리색"] 등 주관적 표현은 가능한 색상 리스트로 확장하세요.
    - 명시되지 않은 속성은 문맥에 맞게 기본 카테고리어로 채우세요.
    """
    
    print("\n" + "=" * 80)
    print(f" 🦙 Ollama 자연어 쿼리 추출 테스트 모드 (모델: {model_name})")
    print(" (종료하려면 'q' 또는 'exit'를 입력하세요)")
    print("=" * 80 + "\n")

    while True:
        try:
            # 사용자로부터 직접 문장 입력 받기
            user_input = input("🔍 검색할 자연어 입력: ").strip()
            
            if user_input.lower() in ["q", "exit", "quit", "종료"]:
                print("\n테스트를 종료합니다.")
                break
                
            if not user_input:
                continue

            print("\n⏳ Ollama 파싱 진행 중...")
            
            # Ollama API 호출 (Structured Output 강제)
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"질의: {user_input}"}
                ],
                format=PersonSearchCondition.model_json_schema(),
                options={"temperature": 0.0}
            )
            
            # JSON 결과 파싱 및 검증
            parsed_dict = json.loads(response.message.content)
            PersonSearchCondition.model_validate(parsed_dict)
            
            # MongoDB 쿼리 변환
            mongo_query = convert_to_mongodb_query(parsed_dict)
            
            # 결과 화면 출력
            print("\n" + "─" * 60)
            print("📌 [1] 추출된 구조화 JSON 데이터 (Pydantic Schema):")
            print(json.dumps(parsed_dict, indent=2, ensure_ascii=False))
            
            print("\n📌 [2] 변환된 MongoDB 필터 쿼리:")
            print(json.dumps(mongo_query, indent=2, ensure_ascii=False))
            print("─" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\n테스트를 종료합니다.")
            break
        except Exception as e:
            print(f"\n❌ [오류 발생]: {e}\n")

if __name__ == "__main__":
    # 로컬에 다운로드된 Ollama 모델명 지정
    run_interactive_parser(model_name="qwen2.5:7b")