import json
import os
import random
import time
from typing import List
from pydantic import BaseModel, Field

# Ollama SDK 불러오기
import ollama

# ==========================================
# 1. Pydantic 스키마 정의
# ==========================================
class ItemCondition(BaseModel):
    category: str = Field(description="항목의 대분류 (상의, 하의, 아우터, 가방, 신발, 모자 등)")
    color: List[str] = Field(description="추출된 색상 목록")
    type: str = Field(description="상세 종류")

class PersonSearchCondition(BaseModel):
    clothing: List[ItemCondition] = Field(default_factory=list)
    accessories: List[ItemCondition] = Field(default_factory=list)

# ==========================================
# 2. 랜덤 질의 생성 함수
# ==========================================
def generate_random_tracking_queries(num_queries=100):
    colors = ["빨간색", "파란색", "검은색", "흰색", "노란색", "회색", "남색", "머스타드색", "초록색"]
    subjective_modifiers = ["어두운", "밝은", "화려한", "눈에 띄는", "칙칙한"]
    upper_types = ["반팔티", "긴팔티", "셔츠", "후드티", "크롭티", "니트"]
    lower_types = ["청바지", "반바지", "면바지", "치마", "미니스커트", "트레이닝복"]
    outer_types = ["아노락", "패딩", "바람막이", "코트", "가디건"]
    accessory_types = ["백팩", "크로스백", "에코백", "벙거지 모자", "야구모자", "캐리어"]
    actions = ["입은 사람 찾아줘", "착용한 여성 검색해", "입고 지나간 남성 찾아", "입은 사람", "착용자 추적해"]
    
    queries = []
    for _ in range(num_queries):
        pattern = random.choice([1, 2, 3, 4])
        get_color = lambda: random.choice(colors) if random.random() > 0.3 else random.choice(subjective_modifiers)
            
        if pattern == 1:
            query = f"{get_color()} {random.choice(upper_types)}에 {get_color()} {random.choice(lower_types)}를 {random.choice(actions)}"
        elif pattern == 2:
            query = f"{get_color()} {random.choice(outer_types)}를 입고 {get_color()} {random.choice(accessory_types)}를 든 사람"
        elif pattern == 3:
            query = f"{get_color()} {random.choice(upper_types)}와 {get_color()} {random.choice(lower_types)} 입고 {random.choice(accessory_types)} 멘 사람 {random.choice(actions)}"
        elif pattern == 4:
            query = f"{random.choice(upper_types)} 입고 {get_color()} {random.choice(accessory_types)} 착용한 사람"
            
        queries.append(query)
    return queries

# ==========================================
# 3. Ollama 기반 대량 파싱 및 성능 평가
# ==========================================
def run_batch_test(num_tests=10, model_name="qwen2.5:7b", output_file="parsing_test_results.json"):
    system_instruction = """
    당신은 지능형 CCTV 검색 질의 분석기입니다.
    사용자의 자연어 묘사에서 '의류'와 '소지품'을 구분하고, 각각의 '색상'과 '종류'를 정확히 분리하여 추출하세요.
    - 색상은 항상 리스트 형태로 반환하세요.
    - 명시되지 않은 속성은 문맥에 맞게 기본 카테고리어로 채우세요.
    """
    
    test_queries = generate_random_tracking_queries(num_tests)
    results_log = []
    success_count = 0
    fail_count = 0
    
    print("\n" + "=" * 80)
    print(f" 🦙 [Ollama - {model_name}] 자연어 파싱 성능 테스트 시작 (총 {num_tests}개 쿼리)")
    print("=" * 80 + "\n")
    
    start_time = time.time()

    for i, query in enumerate(test_queries, 1):
        log_entry = {"id": i, "original_query": query, "status": "", "parsed_data": None, "error": None}
        
        try:
            # Ollama Chat API 호출 (Structured Outputs 적용)
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"질의: {query}"}
                ],
                format=PersonSearchCondition.model_json_schema(),  # Pydantic 스키마 강제
                options={
                    "temperature": 0.0  # 환각 억제
                }
            )
            
            parsed_dict = json.loads(response.message.content)
            PersonSearchCondition.model_validate(parsed_dict)
            
            log_entry["status"] = "SUCCESS"
            log_entry["parsed_data"] = parsed_dict
            success_count += 1
            
            extracted_items = []
            for c in parsed_dict.get("clothing", []):
                extracted_items.append(f"{','.join(c['color'])} {c['type']}")
            for a in parsed_dict.get("accessories", []):
                extracted_items.append(f"{','.join(a['color'])} {a['type']}")
            summary_str = " | ".join(extracted_items) if extracted_items else "추출 항목 없음"

            print(f"[{i:03d}/{num_tests:03d}] ✅ [성공] {query}")
            print(f"        └─ 추출 결과: {summary_str}\n")
            
        except Exception as e:
            fail_count += 1
            log_entry["status"] = "FAILED"
            log_entry["error"] = str(e)
            
            print(f"[{i:03d}/{num_tests:03d}] ❌ [실패] {query}")
            print(f"        └─ 원인: {e}\n")
            
        results_log.append(log_entry)

    elapsed_time = time.time() - start_time
    success_rate = (success_count / num_tests) * 100
    
    print("=" * 80)
    print(f" 📊 Ollama ({model_name}) 파싱 성능 종합 리포트")
    print("=" * 80)
    print(f" • 총 테스트 쿼리 수   : {num_tests} 건")
    print(f" • 성공 건수           : {success_count} 건")
    print(f" • 실패 건수           : {fail_count} 건")
    print(f" • 파싱 성공률         : {success_rate:.2f} %")
    print(f" • 총 소요 시간        : {elapsed_time:.2f} 초 (평균 {elapsed_time/num_tests:.2f}초/건)")
    print("-" * 80)
    
    bar_length = 40
    filled_length = int(bar_length * success_count // num_tests)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    print(f" [성공률 그래프] |{bar}| {success_rate:.1f}%\n")

    summary = {
        "model_used": model_name,
        "total_tests": num_tests,
        "success_count": success_count,
        "fail_count": fail_count,
        "success_rate_percent": success_rate,
        "elapsed_time_sec": round(elapsed_time, 2),
        "details": results_log
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"📁 상세 결과 파일 저장 완료: {os.path.abspath(output_file)}\n")

if __name__ == "__main__":
    # 로컬 Ollama에 다운로드된 모델명 지정 (예: 'qwen2.5:7b', 'llama3.1:8b' 등)
    run_batch_test(num_tests=10, model_name="qwen2.5:7b")