import json
import os
import random
import sqlite3
import time
from typing import List
from pydantic import BaseModel, Field
import ollama

# ==========================================
# 1. Pydantic 스키마 정의
# ==========================================
class ItemCondition(BaseModel):
    category: str = Field(description="항목의 대분류 (상의, 하의, 아우터, 가방, 신발, 모자 등)")
    color: List[str] = Field(description="추출된 색상 목록")
    type: str = Field(description="상세 종류 (예: 반팔티, 청바지, 백팩 등)")

class PersonSearchCondition(BaseModel):
    clothing: List[ItemCondition] = Field(default_factory=list, description="착용한 의류 정보")
    accessories: List[ItemCondition] = Field(default_factory=list, description="소지품 및 악세서리 정보")

# ==========================================
# 2. SQLite 동적 Few-Shot DB 관리 모듈
# ==========================================
DB_PATH = "existing_search_data.db"

def setup_few_shot_db():
    """SQLite DB 초기화 및 기본 학습 예시 생성"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS few_shot_examples
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, natural_query TEXT, parsed_json TEXT)''')
    
    c.execute("SELECT COUNT(*) FROM few_shot_examples")
    if c.fetchone()[0] == 0:
        examples = [
            ("머스타드색 크롭티에 호피무늬 미니스커트를 입고 보라색 백팩을 멘 여성", 
             json.dumps({"clothing": [{"category": "상의", "color": ["머스타드색"], "type": "크롭티"}, {"category": "하의", "color": ["호피무늬"], "type": "미니스커트"}], "accessories": [{"category": "가방", "color": ["보라색"], "type": "백팩"}]}, ensure_ascii=False)),
            ("어두운 아노락 입은 사람 찾아줘", 
             json.dumps({"clothing": [{"category": "아우터", "color": ["검은색", "남색", "회색"], "type": "아노락"}], "accessories": []}, ensure_ascii=False)),
            ("빨간 모자 쓴 사람",
             json.dumps({"clothing": [], "accessories": [{"category": "모자", "color": ["빨간색"], "type": "모자"}]}, ensure_ascii=False))
        ]
        c.executemany("INSERT INTO few_shot_examples (natural_query, parsed_json) VALUES (?, ?)", examples)
        conn.commit()
    return conn

def view_db_examples():
    """DB에 저장된 Few-Shot 예시 조회"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, natural_query, parsed_json FROM few_shot_examples")
    rows = c.fetchall()
    conn.close()
    
    print("\n" + "─" * 60)
    print(" 📂 [Few-Shot DB 학습 데이터 목록]")
    print("─" * 60)
    for r in rows:
        print(f"ID [{r[0]}] 질의: {r[1]}")
        print(f"       파싱: {r[2]}")
    print("─" * 60 + "\n")

def add_db_example(query_text, json_str):
    """새로운 Few-Shot 학습 예시 추가"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO few_shot_examples (natural_query, parsed_json) VALUES (?, ?)", (query_text, json_str))
    conn.commit()
    conn.close()
    print("\n✅ DB에 새로운 학습 데이터가 성공적으로 추가되었습니다!\n")

def fetch_dynamic_examples(limit=3) -> str:
    """프롬프트에 주입할 DB 예시 문자열 가져오기"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT natural_query, parsed_json FROM few_shot_examples ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return "\n".join([f"Input: {r[0]}\nOutput: {r[1]}" for r in rows])

# ==========================================
# 3. 비전 태그 매핑 모듈
# ==========================================
VISION_TAXONOMY_MAP = {
    "category": {"상의": "upper_body", "하의": "lower_body", "아우터": "outerwear", "가방": "bag", "신발": "shoes", "모자": "hat"},
    "color": {"파란색": "blue", "검은색": "black", "빨간색": "red", "흰색": "white", "노란색": "yellow", "회색": "grey", "남색": "navy", "머스타드색": "mustard", "보라색": "purple"},
    "type": {"상의": "shirt", "하의": "pants", "반팔티": "t_shirt", "긴팔티": "long_sleeve", "청바지": "jeans", "미니스커트": "mini_skirt", "크롭티": "crop_top", "아노락": "anorak", "백팩": "backpack"}
}

def map_to_vision_tags(parsed_json: dict) -> dict:
    """추출된 한글 JSON을 비전 모델 영문 태그로 변환"""
    mapped_result = {"clothing": [], "accessories": []}
    for section in ["clothing", "accessories"]:
        for item in parsed_json.get(section, []):
            mapped_colors = [VISION_TAXONOMY_MAP["color"].get(c, c) for c in item.get("color", [])]
            mapped_item = {
                "category": VISION_TAXONOMY_MAP["category"].get(item.get("category"), item.get("category")),
                "color": mapped_colors,
                "type": VISION_TAXONOMY_MAP["type"].get(item.get("type"), item.get("type"))
            }
            mapped_result[section].append(mapped_item)
    return mapped_result

# ==========================================
# 4. MongoDB 쿼리 변환 모듈
# ==========================================
def convert_to_mongodb_query(parsed_json: dict) -> dict:
    """구조화 JSON 데이터를 MongoDB $and / $in 연산자 필터로 변환"""
    and_clauses = []
    for section in ["clothing", "accessories"]:
        for item in parsed_json.get(section, []):
            item_filters = []
            if item.get("category"):
                item_filters.append({f"{section}.category": item["category"]})
            if item.get("color"):
                item_filters.append({f"{section}.color": {"$in": item["color"]}})
            if item.get("type"):
                item_filters.append({f"{section}.type": item["type"]})
            if item_filters:
                and_clauses.append({"$and": item_filters})
    return {"$and": and_clauses} if and_clauses else {}

# ==========================================
# 5. Core Parser Engine (Ollama + Few-Shot DB)
# ==========================================
def parse_natural_language(query: str, model_name="qwen2.5:7b") -> dict:
    """자연어 파싱 메커니즘 실행"""
    dynamic_examples = fetch_dynamic_examples()
    
    system_instruction = f"""
    당신은 지능형 CCTV 검색 질의 분석기입니다.
    사용자의 자연어 묘사에서 '의류'와 '소지품'을 구분하고, 각각의 '색상'과 '종류'를 정확히 분리하여 추출하세요.

    [핵심 규칙]
    1. 환각 방지: 색상과 객체를 완벽히 분리하세요.
    2. 주관적 표현 확장: '어두운' -> ["검은색", "남색", "회색"], '밝은' -> ["흰색", "아이보리색"] 등으로 변환하세요.

    [동적 학습 예시]
    {dynamic_examples}
    """
    
    response = ollama.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"질의: {query}"}
        ],
        format=PersonSearchCondition.model_json_schema(),
        options={"temperature": 0.0}
    )
    
    parsed_dict = json.loads(response.message.content)
    PersonSearchCondition.model_validate(parsed_dict)
    return parsed_dict

# ==========================================
# 6. 대량 배치 테스트 모듈
# ==========================================
def generate_random_tracking_queries(num_queries=10):
    colors = ["빨간색", "파란색", "검은색", "흰색", "노란색", "회색", "남색", "머스타드색", "초록색"]
    subjective_modifiers = ["어두운", "밝은", "화려한", "눈에 띄는", "칙칙한"]
    upper_types = ["반팔티", "긴팔티", "셔츠", "후드티", "크롭티", "니트"]
    lower_types = ["청바지", "반바지", "면바지", "치마", "미니스커트", "트레이닝복"]
    outer_types = ["아노락", "패딩", "바람막이", "코트", "가디건"]
    accessory_types = ["백팩", "크로스백", "에코백", "벙거지 모자", "야구모자", "캐리어"]
    actions = ["입은 사람 찾아줘", "착용한 여성 검색해", "입고 지나간 남성 찾아", "입은 사람", "추적해"]
    
    queries = []
    for _ in range(num_queries):
        pattern = random.choice([1, 2, 3, 4])
        get_color = lambda: random.choice(colors) if random.random() > 0.3 else random.choice(subjective_modifiers)
            
        if pattern == 1:
            query = f"{get_color()} {random.choice(upper_types)}에 {get_color()} {random.choice(lower_types)}를 {random.choice(actions)}"
        elif pattern == 2:
            query = f"{get_color()} {random.choice(outer_types)}를 입고 {get_color()} {random.choice(accessory_types)}를 든 사람"
        elif pattern == 3:
            query = f"{get_color()} {random.choice(upper_types)}와 {get_color()} {random.choice(lower_types)} 입고 {random.choice(accessory_types)} 멘 사람"
        elif pattern == 4:
            query = f"{random.choice(upper_types)} 입고 {get_color()} {random.choice(accessory_types)} 착용한 사람"
            
        queries.append(query)
    return queries

def run_batch_test(num_tests=10, model_name="qwen2.5:7b"):
    test_queries = generate_random_tracking_queries(num_tests)
    results_log = []
    success_count = 0
    fail_count = 0
    
    print("\n" + "=" * 80)
    print(f" 🚀 [대량 테스트 시작] 모델: {model_name} | 수량: {num_tests}개")
    print("=" * 80 + "\n")
    
    start_time = time.time()
    for i, query in enumerate(test_queries, 1):
        log_entry = {"id": i, "original_query": query, "status": "", "parsed_data": None}
        try:
            parsed_dict = parse_natural_language(query, model_name)
            log_entry["status"] = "SUCCESS"
            log_entry["parsed_data"] = parsed_dict
            success_count += 1
            
            extracted = [f"{','.join(c['color'])} {c['type']}" for c in parsed_dict.get("clothing", [])] + \
                        [f"{','.join(a['color'])} {a['type']}" for a in parsed_dict.get("accessories", [])]
            print(f"[{i:02d}/{num_tests:02d}] ✅ [성공] {query}\n       └─ 결과: {' | '.join(extracted)}")
        except Exception as e:
            fail_count += 1
            log_entry["status"] = "FAILED"
            print(f"[{i:02d}/{num_tests:02d}] ❌ [실패] {query}\n       └─ 원인: {e}")
        results_log.append(log_entry)

    elapsed_time = time.time() - start_time
    success_rate = (success_count / num_tests) * 100
    
    print("\n" + "=" * 80)
    print(f" 📊 [대량 파싱 성공률 측정 결과]")
    print(f" • 총 쿼리 수: {num_tests} | 성공: {success_count} | 실패: {fail_count}")
    print(f" • 성공률: {success_rate:.2f}% | 총 소요시간: {elapsed_time:.2f}초")
    print("=" * 80 + "\n")

# ==========================================
# 7. 메인 메뉴 대시보드 (사용자 선택 인터페이스)
# ==========================================
def main_menu():
    setup_few_shot_db()
    model_name = "qwen2.5:7b"
    
    while True:
        print("=" * 70)
        print(" 🛠️  지능형 CCTV 관제 질의 파싱 기능 선택 대시보드")
        print("=" * 70)
        print(" [1] 자연어 파싱 (Pydantic 구조화 JSON 추출)")
        print(" [2] 비전 모델 태그 매핑 (한국어 ➔ 영문 Taxonomy 변환)")
        print(" [3] MongoDB 검색 쿼리 변환 ($and / $in 문법 생성)")
        print(" [4] 올인원 일괄 실행 (자연어 입력 ➔ 파싱 + 비전매핑 + DB쿼리 전체 확인)")
        print(" [5] Few-Shot 예시 DB 관리 (조회 및 신규 예시 학습)")
        print(" [6] 랜덤 대량 배치 테스트 및 성공률 리포트 측정")
        print(" [0] 프로그램 종료")
        print("=" * 70)
        
        choice = input("👉 원하시는 기능의 번호를 입력하세요: ").strip()
        
        if choice == "1":
            q = input("\n🔍 자연어 질의 입력: ").strip()
            if q:
                res = parse_natural_language(q, model_name)
                print("\n📌 [Pydantic 구조화 JSON 추출 결과]:")
                print(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
                
        elif choice == "2":
            q = input("\n🔍 자연어 질의 입력: ").strip()
            if q:
                parsed = parse_natural_language(q, model_name)
                mapped = map_to_vision_tags(parsed)
                print("\n📌 [비전 모델 영문 태그 매핑 결과]:")
                print(json.dumps(mapped, indent=2, ensure_ascii=False) + "\n")
                
        elif choice == "3":
            q = input("\n🔍 자연어 질의 입력: ").strip()
            if q:
                parsed = parse_natural_language(q, model_name)
                mongo_q = convert_to_mongodb_query(parsed)
                print("\n📌 [MongoDB 검색 쿼리 변환 결과]:")
                print(json.dumps(mongo_q, indent=2, ensure_ascii=False) + "\n")
                
        elif choice == "4":
            q = input("\n🔍 자연어 질의 입력: ").strip()
            if q:
                print("\n⏳ Ollama 파싱 및 전체 변환 실행 중...")
                parsed = parse_natural_language(q, model_name)
                mapped = map_to_vision_tags(parsed)
                mongo_q = convert_to_mongodb_query(parsed)
                
                print("\n" + "─" * 60)
                print("1️⃣ Pydantic 구조화 JSON:")
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
                print("\n2️⃣ 비전 모델 영문 태그 매핑:")
                print(json.dumps(mapped, indent=2, ensure_ascii=False))
                print("\n3️⃣ MongoDB 필터 쿼리:")
                print(json.dumps(mongo_q, indent=2, ensure_ascii=False))
                print("─" * 60 + "\n")
                
        elif choice == "5":
            print("\n[Few-Shot DB 관리 메뉴]")
            print("a: 기존 학습 예시 조회")
            print("b: 신규 학습 예시 추가")
            sub_choice = input("선택 (a/b): ").strip().lower()
            if sub_choice == "a":
                view_db_examples()
            elif sub_choice == "b":
                new_q = input("새 자연어 예시: ").strip()
                new_json = input("JSON 결과 텍스트: ").strip()
                if new_q and new_json:
                    add_db_example(new_q, new_json)
                    
        elif choice == "6":
            count_str = input("\n테스트할 쿼리 개수 입력 (기본 10개): ").strip()
            num_t = int(count_str) if count_str.isdigit() else 10
            run_batch_test(num_tests=num_t, model_name=model_name)
            
        elif choice == "0":
            print("\n프로그램을 종료합니다.")
            break
            
        else:
            print("\n❌ 올바른 번호를 선택하세요.\n")

if __name__ == "__main__":
    main_menu()