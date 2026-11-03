import sqlite3
import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional

# ==========================================
# 1. Pydantic 스키마 정의 (구조화된 출력 강제)
# ==========================================
class ItemCondition(BaseModel):
    category: str = Field(description="항목의 대분류 (예: 상의, 하의, 아우터, 가방, 신발)")
    color: List[str] = Field(description="색상 목록. 주관적 표현(어두운, 밝은)은 복수의 구체적 색상으로 치환됨")
    type: str = Field(description="상세 종류 (예: 반팔티, 크롭티, 아노락, 백팩, 벙거지)")

class PersonSearchCondition(BaseModel):
    clothing: List[ItemCondition] = Field(default_factory=list)
    accessories: List[ItemCondition] = Field(default_factory=list)

# ==========================================
# 2. 동적 예시 제어 (SQLite DB 연동)
# ==========================================
def setup_few_shot_db(db_path="existing_search_data.db"):
    """DB를 초기화하고 엣지 케이스 및 주관적 질의 예시를 학습용으로 삽입합니다."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS few_shot_examples
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, natural_query TEXT, parsed_json TEXT)''')
    
    # DB가 비어있을 경우 초기 학습 데이터 삽입
    c.execute("SELECT COUNT(*) FROM few_shot_examples")
    if c.fetchone()[0] == 0:
        examples = [
            ("머스타드색 크롭티에 호피무늬 미니스커트를 입고 보라색 백팩을 멘 여성", 
             json.dumps({"clothing": [{"category": "상의", "color": ["머스타드색"], "type": "크롭티"}, {"category": "하의", "color": ["호피무늬"], "type": "미니스커트"}], "accessories": [{"category": "가방", "color": ["보라색"], "type": "백팩"}]})),
            ("어두운 아노락 입은 사람 찾아줘", 
             json.dumps({"clothing": [{"category": "아우터", "color": ["검은색", "남색", "회색"], "type": "아노락"}], "accessories": []})),
            ("빨간 모자 쓴 사람",
             json.dumps({"clothing": [], "accessories": [{"category": "모자", "color": ["빨간색"], "type": "모자"}]}))
        ]
        c.executemany("INSERT INTO few_shot_examples (natural_query, parsed_json) VALUES (?, ?)", examples)
        conn.commit()
    return conn

def fetch_dynamic_examples(conn, limit=5) -> str:
    """DB에서 쿼리 파싱 예시를 가져와 프롬프트에 주입할 문자열로 변환합니다."""
    c = conn.cursor()
    c.execute("SELECT natural_query, parsed_json FROM few_shot_examples ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    
    few_shot_text = ""
    for row in rows:
        few_shot_text += f"Input: {row[0]}\nOutput: {row[1]}\n\n"
    return few_shot_text

# ==========================================
# 3. 자연어 질의 파싱 엔진 (환각 제어 및 Few-Shot 적용)
# ==========================================
def parse_natural_language_to_json(query: str, db_conn) -> PersonSearchCondition:
    """자연어를 입력받아 동적 예시가 주입된 프롬프트를 통해 Pydantic 객체로 추출합니다."""
    # DB에서 최신 예시 동적 로드
    dynamic_examples = fetch_dynamic_examples(db_conn)
    
    system_instruction = f"""
    당신은 CCTV 관제 시스템의 자연어 질의 파서입니다.
    비구조화된 자연어 인상착의 묘사를 분석하여 정의된 JSON 스키마에 맞게 추출하세요.

    [핵심 규칙]
    1. 환각 방지: 색상과 객체를 완벽히 분리하세요 (예: '빨간 반팔티' -> color: ['빨간색'], type: '반팔티').
    2. Taxonomy 매핑: 비전 모델의 분류에 맞게 카테고리를 통일하세요 (예: 아노락, 패딩 -> '아우터').
    3. 주관적 질의 확장: '어두운 옷' -> ['검은색', '남색', '회색'], '화려한 옷' -> ['빨간색', '노란색', '네온색'] 등으로 치환하세요.

    [학습 예시 (DB 연동)]
    {dynamic_examples}
    """
    
    # Gemini 모델 설정 (temperature=0.0으로 환각 억제, response_schema로 구조 강제)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=system_instruction,
        generation_config=genai.GenerationConfig(
            temperature=0.0, 
            response_mime_type="application/json",
            response_schema=PersonSearchCondition
        )
    )
    
    response = model.generate_content(f"Input: {query}\nOutput:")
    
    # 생성된 JSON 텍스트를 Pydantic 모델로 검증 및 파싱
    parsed_data = PersonSearchCondition.model_validate_json(response.text)
    return parsed_data

# ==========================================
# 4. MongoDB 검색 쿼리 자동 변환 로직
# ==========================================
def build_mongodb_query(parsed_condition: PersonSearchCondition) -> dict:
    """Pydantic으로 구조화된 객체를 MongoDB $and 및 $in 기반 필터 쿼리로 변환합니다."""
    and_clauses = []
    
    # 의류 조건 변환
    for item in parsed_condition.clothing:
        item_query = {"$and": [{"clothing.category": item.category}]}
        if item.color:
            # 여러 색상(주관적 표현 등)이 포함된 경우 $in 연산자 사용
            item_query["$and"].append({"clothing.color": {"$in": item.color}})
        if item.type:
            item_query["$and"].append({"clothing.type": item.type})
        and_clauses.append(item_query)
        
    # 소지품 조건 변환
    for item in parsed_condition.accessories:
        item_query = {"$and": [{"accessories.category": item.category}]}
        if item.color:
            item_query["$and"].append({"accessories.color": {"$in": item.color}})
        if item.type:
            item_query["$and"].append({"accessories.type": item.type})
        and_clauses.append(item_query)
        
    if not and_clauses:
        return {}
        
    return {"$and": and_clauses}

# ==========================================
# 실행 테스트 (End-to-End Test)
# ==========================================
if __name__ == "__main__":
    # API 키 세팅 (실제 환경에서는 환경변수 사용)
    # genai.configure(api_key="YOUR_GEMINI_API_KEY")
    
    # 1. DB 초기화
    db_connection = setup_few_shot_db()
    
    # 2. 복합적이고 주관적인 자연어 쿼리
    test_query = "어두운 벙거지 모자를 쓰고 밝은색 반팔티 입은 사람 찾아줘"
    print(f"[원본 쿼리]: {test_query}\n")
    
    # 3. LLM 기반 자연어 파싱 (DB 예시 동적 주입)
    # API 호출이 필요한 부분이므로 예외처리를 함께 구성하는 것이 좋습니다.
    try:
        parsed_result = parse_natural_language_to_json(test_query, db_connection)
        print("[LLM 구조화 파싱 결과 (Pydantic)]:")
        print(parsed_result.model_dump_json(indent=2))
        print("\n")
        
        # 4. MongoDB 쿼리 변환
        mongo_query = build_mongodb_query(parsed_result)
        print("[최종 MongoDB 쿼리 변환]:")
        print(json.dumps(mongo_query, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"파싱 중 오류 발생 (API 키 확인 필요): {e}")