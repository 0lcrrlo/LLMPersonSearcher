from person_searcher.domain.models import ItemCondition, PersonSearchCondition
from person_searcher.domain.taxonomy import normalize_condition
from person_searcher.query.builder import build_mongo_query
from person_searcher.query.ollama_parser import OllamaQueryParser
from person_searcher.evaluation.queries import generate_tracking_queries
from person_searcher.storage.few_shot import FewShotStore


def test_query_uses_elem_match_for_each_item():
    condition = PersonSearchCondition(
        clothing=[
            ItemCondition(category="upper_body", colors=["blue"], item_type="t_shirt")
        ]
    )
    assert build_mongo_query(condition) == {
        "$and": [
            {
                "clothing": {
                    "$elemMatch": {
                        "category": "upper_body",
                        "color": {"$in": ["blue"]},
                        "type": "t_shirt",
                    }
                }
            }
        ]
    }


def test_taxonomy_normalizes_existing_korean_parser_output():
    condition = PersonSearchCondition(
        clothing=[ItemCondition(category="상의", colors=["파란색"], item_type="반팔티")]
    )
    normalized = normalize_condition(condition)
    assert normalized.clothing[0].model_dump() == {
        "category": "upper_body",
        "colors": ["blue"],
        "item_type": "t_shirt",
    }


def test_few_shot_store_round_trip(tmp_path):
    store = FewShotStore(tmp_path / "examples.db")
    store.initialize()
    examples = store.fetch()
    assert len(examples) == 3
    assert examples[0][1].clothing or examples[0][1].accessories


def test_generated_queries_are_reproducible():
    first = generate_tracking_queries(5, seed=7)
    assert first == generate_tracking_queries(5, seed=7)
    assert len(first) == 5


def test_ollama_parser_validates_and_normalizes_response(tmp_path):
    class FakeClient:
        def chat(self, **kwargs):
            class Message:
                content = (
                    '{"clothing":[{"category":"상의","colors":["파란색"],'
                    '"item_type":"반팔티"}],"accessories":[]}'
                )

            class Response:
                message = Message()

            return Response()

    store = FewShotStore(tmp_path / "examples.db")
    store.initialize()
    parsed = OllamaQueryParser(client=FakeClient(), examples=store).parse("파란 상의")
    assert parsed.clothing[0].category == "upper_body"
    assert parsed.clothing[0].colors == ["blue"]


def test_legacy_prototype_field_names_are_accepted():
    condition = PersonSearchCondition.model_validate(
        {
            "clothing": [
                {"category": "상의", "color": ["파란색"], "type": "반팔티"}
            ]
        }
    )
    assert condition.clothing[0].colors == ["파란색"]
    assert condition.clothing[0].item_type == "반팔티"
