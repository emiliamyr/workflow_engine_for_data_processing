import pytest

from workflow_engine.components import (
    InMemoryExtractor,
    ListLoader,
    SelectColumnsTransformer,
)


def test_in_memory_extractor_yields_batches() -> None:
    extractor = InMemoryExtractor(
        [{"id": 1}, {"id": 2}, {"id": 3}],
    )

    assert list(extractor.extract(batch_size=2)) == [
        [{"id": 1}, {"id": 2}],
        [{"id": 3}],
    ]


def test_in_memory_extractor_rejects_invalid_batch_size() -> None:
    extractor = InMemoryExtractor([])

    with pytest.raises(ValueError, match="greater than zero"):
        list(extractor.extract(batch_size=0))


def test_pipeline_processes_data_in_batches() -> None:
    extractor = InMemoryExtractor(
        [
            {"name": "Ada", "active": True},
            {"name": "Grace", "active": False},
        ],
    )
    transformer = SelectColumnsTransformer(["name"])
    loader = ListLoader()

    batches = extractor.extract(batch_size=1)
    transformed_batches = (transformer.transform(batch) for batch in batches)

    assert loader.load(transformed_batches) == [
        {"name": "Ada"},
        {"name": "Grace"},
    ]
