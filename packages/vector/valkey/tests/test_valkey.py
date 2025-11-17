import uuid

from dotenv import load_dotenv

load_dotenv()  # loads .env from current directory

from glide import ft
from glide_shared.constants import OK

from cognee_community_vector_adapter_valkey.valkey_adapter import ValkeyAdapter, MissingQueryParameterError
from cognee.infrastructure.engine import DataPoint
from cognee.infrastructure.databases.vector import get_vector_engine

import os
import pytest
from cognee import config

from cognee_community_vector_adapter_valkey import register

class MyChunk(DataPoint):
    text: str
    metadata: dict = {
        "type": "DocumentChunk",
        "index_fields": ["text"],
    }

@pytest.fixture(autouse=True)
def setup_cognee_config(tmp_path):
    # Use a temporary directory for system and data roots
    system_path = tmp_path / ".cognee-system"
    data_path = tmp_path / ".cognee-data"
    system_path.mkdir()
    data_path.mkdir()

    config.system_root_directory(str(system_path))
    config.data_root_directory(str(data_path))

    # Set vector DB config for Valkey
    config.set_vector_db_config(
        {
            "vector_db_provider": "valkey",
            "vector_db_url": os.getenv("VECTOR_DB_URL", "valkey://localhost:6379"),
            "vector_db_key": os.getenv("VECTOR_DB_KEY", "your-api-key"),
        }
    )

async def test_valkey_path():
    vector_engine = get_vector_engine()
    client = await vector_engine.get_connection()
    collection = "my_collection-" + str(uuid.uuid4())

    # Create collection
    await vector_engine.create_collection(collection)

    # Verify collection created
    info = await ft.info(client, vector_engine._index_name(collection))
    assert (info is not None)

    # Insert a couple of points
    id_1 = uuid.uuid4()
    id_2 = uuid.uuid4()
    data_points = [
        MyChunk(id=id_1, text="Hello Valkey"),
        MyChunk(id=id_2, text="Ollama local embeddings are neat"),
    ]
    await vector_engine.create_data_points(collection, data_points)

    # Text search (the adapter should embed the query via the same engine)
    results = await vector_engine.search(
        collection_name=collection,
        query_text="Hello",
        limit=10
    )

    assert len(results) == 2
    assert [r.id for r in results] == [id_1, id_2]

    assert await ft.dropindex(client, vector_engine._index_name(collection)) == OK


async def test_empty_collection_search_returns_no_results():
    vector_engine: ValkeyAdapter = get_vector_engine()
    client = await vector_engine.get_connection()
    collection = f"empty_search_{uuid.uuid4()}"

    await vector_engine.create_collection(collection_name=collection)
    results = await vector_engine.search(collection_name=collection, query_text="Nonexistent", limit=10)

    assert results == []
    assert await ft.dropindex(client, vector_engine._index_name(collection)) == OK


async def test_search_invalid_collection_returns_no_results():
    vector_engine = get_vector_engine()

    results = await vector_engine.search(collection_name="does_not_exist", query_text="Hello", limit=10)
    assert results == []


async def test_search_empty_query_text():
    vector_engine = get_vector_engine()
    client = await vector_engine.get_connection()
    collection = f"empty_search_{uuid.uuid4()}"

    await vector_engine.create_collection(collection)

    with pytest.raises(MissingQueryParameterError):
        await vector_engine.search(collection_name=collection, query_text=None, limit=10)

    assert await ft.dropindex(client, vector_engine._index_name(collection)) == OK


async def test_delete_data_points():
    vector_engine = get_vector_engine()
    client = await vector_engine.get_connection()
    collection = f"delete_data_points_{uuid.uuid4()}"

    id_1 = uuid.uuid4()
    id_2 = uuid.uuid4()
    data_points = [
        MyChunk(id=id_1, text="Hello Valkey"),
        MyChunk(id=id_2, text="Ollama local embeddings are neat"),
    ]

    await vector_engine.create_collection(collection_name=collection)

    # Insert a couple of points
    await vector_engine.create_data_points(collection, data_points)

    # Text search (the adapter should embed the query via the same engine)
    results = await vector_engine.search(collection_name=collection, query_text="Hello", limit=10)
    assert len(results) == 2

    # Delete data points
    await vector_engine.delete_data_points(collection, [id_1, id_2])
    results = await vector_engine.search(collection_name=collection, query_text="Hello", limit=10)
    assert len(results) == 0

    # Insert data points again
    await vector_engine.create_data_points(collection, data_points)

    # Delete data points
    await vector_engine.delete_data_points(collection, [id_1])
    results = await vector_engine.search(collection_name=collection, query_text="Hello", limit=10)
    assert len(results) == 1
    assert [r.id for r in results] == [id_2]

    assert await ft.dropindex(client, vector_engine._index_name(collection)) == OK


async def test_retrieve_data_points():
    vector_engine = get_vector_engine()
    client = await vector_engine.get_connection()
    collection = f"delete_data_points_{uuid.uuid4()}"

    id_1 = uuid.uuid4()
    id_2 = uuid.uuid4()
    data_points = [
        MyChunk(id=id_1, text="Hello Valkey"),
        MyChunk(id=id_2, text="Ollama local embeddings are neat"),
    ]

    await vector_engine.create_collection(collection)

    # Insert a couple of points
    await vector_engine.create_data_points(collection, data_points)

    # Retrieve data points
    results = await vector_engine.retrieve(collection, [id_1])
    print(f"TestLog: retrieve: {results}")
    assert len(results) == 1
    assert [r['id'] for r in results] == [str(id_1)]

    # Retrieve data points again
    results = await vector_engine.retrieve(collection, [id_1, id_2])
    assert len(results) == 2
    assert [r['id'] for r in results] == [str(id_1), str(id_2)]


async def test_valkey_connection():
    vector_engine = get_vector_engine()
    client = await vector_engine.get_connection()

    assert client is not None
    assert (await client.ping()) in (b"PONG", "PONG")
