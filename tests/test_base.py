import importlib.util

import pytest

import workflow_engine
from workflow_engine.base import BaseExtractor, BaseLoader, BaseTransformer


@pytest.mark.parametrize(
    "name",
    ["BaseExtractor", "BaseLoader", "BaseTransformer", "DEFAULT_BATCH_SIZE"],
)
def test_base_exports_are_not_at_top_level(name: str) -> None:
    assert not hasattr(workflow_engine, name)


@pytest.mark.parametrize("name", ["extractor", "loader", "transformer", "types"])
def test_base_implementation_modules_are_private(name: str) -> None:
    assert importlib.util.find_spec(f"workflow_engine.base.{name}") is None


@pytest.mark.parametrize("base_class", [BaseExtractor, BaseTransformer, BaseLoader])
def test_base_components_are_abstract(base_class: type[object]) -> None:
    with pytest.raises(TypeError):
        base_class()


def test_base_component_methods_raise_not_implemented() -> None:
    class ExampleExtractor(BaseExtractor):
        def extract(self, batch_size: int = 100):
            return super().extract(batch_size)  # pyright: ignore[reportAbstractUsage]

    with pytest.raises(NotImplementedError):
        ExampleExtractor().extract()
