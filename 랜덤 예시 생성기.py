import random

def generate_random_tracking_queries(num_queries=5):
    """
    CCTV 관제 모듈의 LLM 파싱 테스트를 위한 랜덤 자연어 질의를 생성합니다.
    """
    
    # 1. 테스트를 위한 어휘 풀(Pool) 정의
    colors = ["빨간색", "파란색", "검은색", "흰색", "노란색", "회색", "남색", "머스타드색", "초록색"]
    subjective_modifiers = ["어두운", "밝은", "화려한", "눈에 띄는", "칙칙한"]
    
    upper_types = ["반팔티", "긴팔티", "셔츠", "후드티", "크롭티", "니트"]
    lower_types = ["청바지", "반바지", "면바지", "치마", "미니스커트", "트레이닝복"]
    outer_types = ["아노락", "패딩", "바람막이", "코트", "가디건"]
    
    accessory_types = ["백팩", "크로스백", "에코백", "벙거지 모자", "야구모자", "캐리어"]
    
    actions = ["입은 사람 찾아줘", "착용한 여성 검색해", "입고 지나간 남성 찾아", "입은 사람", "착용자 추적해"]
    
    queries = []
    
    for _ in range(num_queries):
        # 질의 패턴 랜덤 선택
        pattern = random.choice([1, 2, 3, 4])
        
        # 색상 또는 주관적 표현 랜덤 선택 함수
        def get_color():
            return random.choice(colors) if random.random() > 0.3 else random.choice(subjective_modifiers)
            
        if pattern == 1:
            # 상의 + 하의 조합
            query = f"{get_color()} {random.choice(upper_types)}에 {get_color()} {random.choice(lower_types)}를 {random.choice(actions)}"
            
        elif pattern == 2:
            # 아우터 단일 + 소지품 조합
            query = f"{get_color()} {random.choice(outer_types)}를 입고 {get_color()} {random.choice(accessory_types)}를 든 사람"
            
        elif pattern == 3:
            # 상의 + 하의 + 소지품 복합 조합 (엣지 케이스 테스트용)
            query = f"{get_color()} {random.choice(upper_types)}와 {get_color()} {random.choice(lower_types)} 입고 {random.choice(accessory_types)} 멘 사람 {random.choice(actions)}"
            
        elif pattern == 4:
            # 색상 생략 등 불완전한 쿼리 (LLM의 추론 능력 테스트)
            query = f"{random.choice(upper_types)} 입고 {get_color()} {random.choice(accessory_types)} 착용한 사람"
            
        queries.append(query)
        
    return queries

# --- 실행 테스트 ---
if __name__ == "__main__":
    print("[랜덤 자연어 질의 생성 결과]")
    print("-" * 40)
    
    test_queries = generate_random_tracking_queries(10)
    
    for i, q in enumerate(test_queries, 1):
        print(f"Test {i}: {q}")