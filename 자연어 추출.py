import os
import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List

# ==========================================
# 1. 추출할 데이터 구조 정의 (Pydantic)
# ==========================================
class ItemCondition(BaseModel):
    category: str = Field(description="항목의 대분류 (상의, 하의, 아우터, 가방, 신발, 모자 등)")
    color: List[str] = Field(description="추출된 색상 목록 (예: ['파란색'], ['검은색'])")
    type: str = Field(description="상세 종류 (예: 셔츠, 바지, 티셔츠 등, 모를 경우 '옷' 또는 카테고리명)")

class PersonSearchCondition(BaseModel):
    clothing: List[ItemCondition] = Field(default_factory=list, description="착용한 의류 정보")
    accessories: List[ItemCondition] = Field(default_factory=list, description="소지품 또는 악세서리 정보")

# ==========================================
# 2. 자연어 쿼리 추출 함수
# ==========================================
def extract_query_from_natural_language(query: str) -> str:
    """자연어를 분석하여 색상과 의류 종류가 분리된 JSON 형태의 쿼리로 추출합니다."""
    
    # API 키 설정 (실행 환경에 맞게 변경 필요)
    # genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    
    system_instruction = """
    당신은 지능형 CCTV 검색 질의 분석기입니다.
    사용자의 자연어 묘사에서 '의류'와 '소지품'을 구분하고, 각각의 '색상'과 '종류'를 정확히 분리하여 추출하세요.
    - 색상은 항상 리스트 형태로 반환하세요 (예: "파란" -> ["파란색"]).
    - 명시되지 않은 속성은 문맥에 맞게 기본 카테고리어로 채우세요.
    """
    
    # 모델 설정: 환각 억제(temperature 0.0) 및 JSON 스키마 강제
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=system_instruction,
        generation_config=genai.GenerationConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=PersonSearchCondition
        )
    )
    
    # LLM에 질의 요청
    response = model.generate_content(f"질의: {query}")
    
    return response.text

# ==========================================
# 3. 테스트 실행
# ==========================================
if __name__ == "__main__":
    # 테스트 질의
    user_input = "파란 상의에 검은 하의를 입은 사람을 찾아줘"
    
    try:
        # 추출 실행 (API 연동 시 주석 해제하여 테스트)
        # result_json_str = extract_query_from_natural_language(user_input)
        
        # [가상 실행 결과 출력] - 실제 API 응답과 동일한 형태
        simulated_result = {
            "clothing": [
                {
                    "category": "상의",
                    "color": ["파란색"],
                    "type": "상의"
                },
                {
                    "category": "하의",
                    "color": ["검은색"],
                    "type": "하의"
                }
            ],
            "accessories": []
        }
        
        print(f"[입력된 자연어]: {user_input}\n")
        print("[추출된 정형화 쿼리 (JSON)]:")
        print(json.dumps(simulated_result, indent=2, ensure_ascii=False))
        
        # Pydantic 모델로 파싱 및 검증
        parsed_obj = PersonSearchCondition.model_validate(simulated_result)
        
        # MongoDB 쿼리화 등 후속 처리...
        
    except Exception as e:
        print(f"오류 발생: {e}")