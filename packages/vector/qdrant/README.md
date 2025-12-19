# Cognee Qdrant Adapter

## Installation

If published, the package can be simply installed via pip:

```bash
pip install cognee-community-vector-adapter-qdrant
```

In case it is not published yet, you can use poetry to locally build the adapter package:

```bash
pip install poetry
poetry install # run this command in the directory containing the pyproject.toml file
```

## Connection Setup

For a quick local setup, you can run a docker container that qdrant provides (https://qdrant.tech/documentation/quickstart/). 
After this, you will be able to connect to the Qdrant DB through the appropriate ports. The command for running the docker 
container looks something like the following:

```
docker run -p 6333:6333 -p 6334:6334 \
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant
```

## Usage

Import and register the adapter in your code:
```python
from cognee_community_vector_adapter_qdrant import register
```

Also, specify the dataset handler in the .env file:
```dotenv
VECTOR_DATASET_DATABASE_HANDLER="qdrant"
```

## Example
See example in `example.py` file.
