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
    with pytest.raises(ValueError, match="greater than zero"):
        list(extractor.extract(batch_size=-1))


def test_empty_in_memory_extractor_yields_no_batches() -> None:
    assert list(InMemoryExtractor([]).extract()) == []


def test_batch_size_larger_than_data_yields_one_batch() -> None:
    extractor = InMemoryExtractor([{"id": 1}])

    assert list(extractor.extract(batch_size=100)) == [[{"id": 1}]]


def test_select_columns_transformer_keeps_only_selected_columns() -> None:
    transformer = SelectColumnsTransformer(["name"])

    assert transformer.transform(
        [
            {"name": "Ada", "age": 36},
            {"name": "Grace", "age": 28},
        ],
    ) == [
        {"name": "Ada"},
        {"name": "Grace"},
    ]


def test_select_columns_transformer_ignores_missing_columns() -> None:
    transformer = SelectColumnsTransformer(["name", "email"])

    assert transformer.transform([{"name": "Ada"}]) == [{"name": "Ada"}]


def test_list_loader_flattens_batches() -> None:
    loader = ListLoader()

    assert loader.load(
        [
            [{"id": 1}, {"id": 2}],
            [{"id": 3}],
        ],
    ) == [
        {"id": 1},
        {"id": 2},
        {"id": 3},
    ]


def test_list_loader_handles_empty_batches() -> None:
    assert ListLoader().load([]) == []


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
