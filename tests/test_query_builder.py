from person_searcher.domain.models import ItemCondition, PersonSearchCondition
from person_searcher.domain.taxonomy import normalize_condition
from person_searcher.query.builder import build_mongo_query
from person_searcher.query.ollama_parser import OllamaQueryParser
from person_searcher.evaluation.queries import generate_tracking_queries
from person_searcher.storage.few_shot import FewShotStore
from person_searcher.ingestion.annotations import AnnotationReader
from person_searcher.ingestion.cropper import CropWriter
from person_searcher.storage.sqlite import SQLiteStore


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


def test_event_ingestion_preserves_event_metadata_and_indexes(tmp_path):
    root = tmp_path / "Training" / "배회"
    labels = root / "[라벨]배회_1"
    images = root / "[원천]배회_1" / "1"
    labels.mkdir(parents=True)
    images.mkdir(parents=True)
    from PIL import Image

    image_name = "frame_1.jpg"
    Image.new("RGB", (100, 100), "white").save(images / image_name)
    (labels / "annotation_1.json").write_text(
        '{"file":"video-1.mp4","frames":[{"number":1,"image":"frame_1.jpg",'
        '"annotations":[{"label":{"x":10,"y":20,"width":30,"height":40},'
        '"category":{"code":"person","attributes":[]}}]}]}',
        encoding="utf-8",
    )

    record = next(AnnotationReader(root, root).records())
    assert record["split"] == "training"
    assert record["event_class"] == "배회"
    crop = CropWriter(tmp_path / "crops").write(record)
    store = SQLiteStore(tmp_path / "search.db")
    store.initialize()
    store.add_detection(record, crop)
    store.add_detection(record, crop)

    import sqlite3

    with sqlite3.connect(tmp_path / "search.db") as db:
        assert db.execute("SELECT COUNT(*) FROM person_detection").fetchone()[0] == 1
        assert db.execute(
            "SELECT event_class, split, category FROM person_detection"
        ).fetchone() == ("배회", "training", "person")
