import json

# 비전 모델 클래스와의 매핑을 위한 Taxonomy 딕셔너리
VISION_TAXONOMY_MAP = {
    "category": {
        "상의": "upper_body",
        "하의": "lower_body",
        "아우터": "outerwear",
        "가방": "bag",
        "신발": "shoes",
        "모자": "hat"
    },
    "color": {
        "파란색": "blue",
        "검은색": "black",
        "빨간색": "red",
        "흰색": "white",
        "노란색": "yellow",
        "회색": "grey",
        "남색": "navy"
    },
    "type": {
        "상의": "shirt",
        "하의": "pants",
        "반팔티": "t_shirt",
        "긴팔티": "long_sleeve",
        "청바지": "jeans",
        "반바지": "shorts",
        "백팩": "backpack",
        "크로스백": "cross_bag"
    }
}

def map_to_vision_tags(parsed_json: dict) -> dict:
    """
    LLM이 추출한 한글 속성(색상, 종류)을 비전 모델이 사용하는 
    영문 태그셋(Taxonomy)으로 치환하여 반환합니다.
    """
    mapped_result = {"clothing": [], "accessories": []}
    
    for section in ["clothing", "accessories"]:
        for item in parsed_json.get(section, []):
            
            # 색상 배열 매핑 (사전에 없으면 기본값 'unknown_color' 처리)
            mapped_colors = [
                VISION_TAXONOMY_MAP["color"].get(c, "unknown_color") 
                for c in item.get("color", [])
            ]
            
            mapped_item = {
                "category": VISION_TAXONOMY_MAP["category"].get(item.get("category"), "unknown_category"),
                "color": mapped_colors,
                "type": VISION_TAXONOMY_MAP["type"].get(item.get("type"), "unknown_type")
            }
            mapped_result[section].append(mapped_item)
            
    return mapped_result

# --- 실행 테스트 ---
if __name__ == "__main__":
    sample_parsed_data = {
        "clothing": [
            {"category": "상의", "color": ["파란색"], "type": "반팔티"},
            {"category": "하의", "color": ["검은색"], "type": "청바지"}
        ],
        "accessories": []
    }
    
    vision_mapped_data = map_to_vision_tags(sample_parsed_data)
    print("[비전 모델 태그 매핑 결과]")
    print(json.dumps(vision_mapped_data, indent=2, ensure_ascii=False))