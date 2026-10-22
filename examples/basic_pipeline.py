"""Run a manual Extractor -> Transformer -> Loader pipeline."""

import pandas as pd

from workflow_engine import (
    InMemoryExtractor,
    ListLoader,
    SelectColumnsTransformer,
)

data = pd.DataFrame(
    {
        "name": ["Ada", "Grace", "Alan"],
        "role": ["engineer", "scientist", "mathematician"],
        "active": [True, True, False],
    },
)

extractor = InMemoryExtractor(data)
transformer = SelectColumnsTransformer(["name", "role"])
loader = ListLoader()

print("Batches from extractor:")
batches = extractor.extract(batch_size=2)


def transform_batches():
    for batch in batches:
        print(f"  input:  {batch}")
        transformed = transformer.transform(batch)
        print(f"  output: {transformed}")
        yield transformed


result = loader.load(transform_batches())

print("\nLoaded records:")
print(result)
