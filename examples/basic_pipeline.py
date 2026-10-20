"""Run a manual Extractor -> Transformer -> Loader pipeline."""

from workflow_engine import (
    InMemoryExtractor,
    ListLoader,
    SelectColumnsTransformer,
)

records = [
    {"name": "Ada", "role": "engineer", "active": True},
    {"name": "Grace", "role": "scientist", "active": True},
    {"name": "Alan", "role": "mathematician", "active": False},
]

extractor = InMemoryExtractor(records)
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
for record in result:
    print(f"  {record}")
