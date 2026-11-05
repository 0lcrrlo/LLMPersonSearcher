import random
from typing import List, Optional


def generate_tracking_queries(
    count: int = 10, seed: Optional[int] = None
) -> List[str]:
    """Generate reproducible parser test queries from the prototype vocabulary."""

    if count < 0:
        raise ValueError("count must be >= 0")
    rng = random.Random(seed)
    colors = ["빨간색", "파란색", "검은색", "흰색", "노란색", "회색", "남색"]
    subjective = ["어두운", "밝은", "화려한", "칙칙한"]
    upper = ["반팔티", "긴팔티", "셔츠", "후드티", "크롭티", "니트"]
    lower = ["청바지", "반바지", "면바지", "치마", "미니스커트"]
    outer = ["아노락", "패딩", "바람막이", "코트", "가디건"]
    accessories = ["백팩", "크로스백", "에코백", "벙거지 모자", "야구모자"]
    actions = ["입은 사람 찾아줘", "착용자 찾아줘", "입고 지나간 사람 찾아줘"]

    def color() -> str:
        return rng.choice(colors + subjective[:2])

    queries = []
    for _ in range(count):
        pattern = rng.randrange(4)
        if pattern == 0:
            queries.append(
                f"{color()} {rng.choice(upper)}에 {color()} "
                f"{rng.choice(lower)}를 {rng.choice(actions)}"
            )
        elif pattern == 1:
            queries.append(
                f"{color()} {rng.choice(outer)}를 입고 "
                f"{color()} {rng.choice(accessories)}를 든 사람"
            )
        elif pattern == 2:
            queries.append(
                f"{color()} {rng.choice(upper)}와 {color()} "
                f"{rng.choice(lower)} 입고 {rng.choice(accessories)} 멘 사람"
            )
        else:
            queries.append(
                f"{rng.choice(upper)} 입고 {color()} "
                f"{rng.choice(accessories)} 착용한 사람"
            )
    return queries
