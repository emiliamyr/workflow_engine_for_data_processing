import pytest

from workflow_engine import BaseExtractor, BaseLoader, BaseTransformer


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
