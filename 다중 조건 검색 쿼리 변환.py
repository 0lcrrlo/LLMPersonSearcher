import json

def convert_to_mongodb_query(parsed_json: dict) -> dict:
    """
    LLM에서 추출된 구조화된 JSON(의류, 소지품)을 
    MongoDB $and 및 $in 검색 쿼리로 자동 변환합니다.
    """
    and_clauses = []
    
    # 1. 의류(clothing) 조건 변환
    for item in parsed_json.get("clothing", []):
        item_filters = []
        
        if item.get("category"):
            item_filters.append({"clothing.category": item["category"]})
        
        # 색상은 리스트 형태이므로 $in 연산자 활용 (여러 색상 중 하나라도 일치하면 검색)
        if item.get("color"):
            item_filters.append({"clothing.color": {"$in": item["color"]}})
            
        if item.get("type"):
            item_filters.append({"clothing.type": item["type"]})
            
        # 해당 의류 아이템에 대한 조건이 존재하면 통째로 묶어서 and_clauses에 추가
        if item_filters:
            and_clauses.append({"$and": item_filters})
            
    # 2. 소지품(accessories) 조건 변환
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
            
    # 조건이 전혀 없는 경우 빈 딕셔너리 반환
    if not and_clauses:
        return {}
        
    return {"$and": and_clauses}

# --- 실행 테스트 ---
if __name__ == "__main__":
    sample_parsed_data = {
        "clothing": [
            {"category": "상의", "color": ["파란색"], "type": "상의"},
            {"category": "하의", "color": ["검은색"], "type": "하의"}
        ],
        "accessories": []
    }
    
    mongo_query = convert_to_mongodb_query(sample_parsed_data)
    print("[MongoDB 쿼리 변환 결과]")
    print(json.dumps(mongo_query, indent=2, ensure_ascii=False))