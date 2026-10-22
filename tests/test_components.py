import pandas as pd
import pytest

from workflow_engine.components import (
    InMemoryExtractor,
    ListLoader,
    SelectColumnsTransformer,
)


def test_in_memory_extractor_yields_batches() -> None:
    extractor = InMemoryExtractor(
        pd.DataFrame({"id": [1, 2, 3]}),
    )

    batches = list(extractor.extract(batch_size=2))
    pd.testing.assert_frame_equal(batches[0], pd.DataFrame({"id": [1, 2]}))
    pd.testing.assert_frame_equal(
        batches[1],
        pd.DataFrame({"id": [3]}, index=[2]),
    )


def test_in_memory_extractor_rejects_invalid_batch_size() -> None:
    extractor = InMemoryExtractor(pd.DataFrame())

    with pytest.raises(ValueError, match="greater than zero"):
        list(extractor.extract(batch_size=0))
    with pytest.raises(ValueError, match="greater than zero"):
        list(extractor.extract(batch_size=-1))


def test_empty_in_memory_extractor_yields_no_batches() -> None:
    assert list(InMemoryExtractor(pd.DataFrame()).extract()) == []


def test_batch_size_larger_than_data_yields_one_batch() -> None:
    extractor = InMemoryExtractor(pd.DataFrame({"id": [1]}))

    batches = list(extractor.extract(batch_size=100))
    pd.testing.assert_frame_equal(batches[0], pd.DataFrame({"id": [1]}))


def test_select_columns_transformer_keeps_only_selected_columns() -> None:
    transformer = SelectColumnsTransformer(["name"])

    result = transformer.transform(
        pd.DataFrame(
            {
                "name": ["Ada", "Grace"],
                "age": [36, 28],
            },
        ),
    )
    pd.testing.assert_frame_equal(result, pd.DataFrame({"name": ["Ada", "Grace"]}))


def test_select_columns_transformer_ignores_missing_columns() -> None:
    transformer = SelectColumnsTransformer(["name", "email"])

    result = transformer.transform(pd.DataFrame({"name": ["Ada"]}))
    pd.testing.assert_frame_equal(result, pd.DataFrame({"name": ["Ada"]}))


def test_list_loader_flattens_batches() -> None:
    loader = ListLoader()

    result = loader.load(
        [
            pd.DataFrame({"id": [1, 2]}),
            pd.DataFrame({"id": [3]}),
        ],
    )
    pd.testing.assert_frame_equal(result, pd.DataFrame({"id": [1, 2, 3]}))


def test_list_loader_handles_empty_batches() -> None:
    result = ListLoader().load([])
    pd.testing.assert_frame_equal(result, pd.DataFrame())


def test_pipeline_processes_data_in_batches() -> None:
    extractor = InMemoryExtractor(
        pd.DataFrame(
            {
                "name": ["Ada", "Grace"],
                "active": [True, False],
            },
        ),
    )
    transformer = SelectColumnsTransformer(["name"])
    loader = ListLoader()

    batches = extractor.extract(batch_size=1)
    transformed_batches = (transformer.transform(batch) for batch in batches)

    result = loader.load(transformed_batches)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"name": ["Ada", "Grace"]}))
