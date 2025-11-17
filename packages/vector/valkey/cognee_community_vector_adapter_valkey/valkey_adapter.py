from __future__ import annotations

import asyncio
import json
import struct
from typing import Any
from uuid import UUID
from urllib.parse import urlparse

from cognee.infrastructure.databases.exceptions import MissingQueryParameterError
from cognee.infrastructure.databases.vector import VectorDBInterface
from cognee.infrastructure.databases.vector.embeddings.EmbeddingEngine import (
    EmbeddingEngine,
)
from cognee.infrastructure.databases.vector.models.ScoredResult import ScoredResult
from cognee.infrastructure.engine import DataPoint
from cognee.infrastructure.engine.utils import parse_id
from cognee.shared.logging_utils import get_logger
# ---- Valkey GLIDE (async) ----------------------------------------------------
# Docs: https://valkey.io/valkey-glide/
from glide import (
    GlideClient,
    GlideClientConfiguration,
    GlideClusterClient,
    GlideClusterClientConfiguration,
    NodeAddress,
    ft,  # Full-text (Valkey‑Search) helpers
    glide_json,
    FtSearchOptions,
    ReturnField,
    BackoffStrategy
)
from glide_shared.commands.server_modules.ft_options.ft_create_options import (
    DataType,
    DistanceMetricType,
    Field,
    FtCreateOptions,
    NumericField,
    TagField,
    TextField,
    VectorAlgorithm,
    VectorField,
    VectorFieldAttributesFlat,
    VectorFieldAttributesHnsw,
    VectorType,
)
from glide_shared.commands.server_modules.ft_options.ft_search_options import (
    FtSearchOptions,
    ReturnField,
)
from glide_shared.exceptions import RequestError

logger = get_logger("ValkeyAdapter")


# -------------------------- helpers & utilities -------------------------------

class ValkeyVectorEngineInitializationError(Exception):
    """Exception raised when vector engine initialization fails."""

    pass


class CollectionNotFoundError(Exception):
    """Exception raised when a collection is not found."""

    pass


def parse_host_port(url: str) -> tuple[str, int]:
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    return host, port

def _to_float32_bytes(vec) -> bytes:
    return struct.pack(f"{len(vec)}f", *map(float, vec))


def serialize_for_json(obj: Any) -> Any:
    if isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj


def _b2s(x: Any) -> Any:
    if isinstance(x, (bytes, bytearray)):
        try:
            return x.decode("utf-8")
        except Exception:
            return str(x)
    return x


def build_scored_results_from_ft(
        raw: Any,
        *,
        use_key_suffix_when_missing_id: bool = True,
) -> list["ScoredResult"]:
    if not isinstance(raw, (list, tuple)) or len(raw) < 2 or not isinstance(raw[1], dict):
        return []

    mapping: dict[Any, dict[Any, Any]] = raw[1]  # the { key -> fields } dict
    scored: list[ScoredResult] = []

    for key_bytes, fields in mapping.items():
        key_str = _b2s(key_bytes)

        # Extract id
        raw_id = fields.get(b"id") if b"id" in fields else fields.get("id")
        if raw_id is not None:
            result_id = _b2s(raw_id)
        else:
            result_id = key_str

        # Extrat score
        score = fields.get(b"__vector_score") if b"__vector_score" in fields else fields.get("__vector_score")
        if score is not None:
            score = float(score)

        # Extract and parse payload_data
        payload_raw = fields.get(b"payload_data") if b"payload_data" in fields else fields.get("payload_data")
        payload: dict[str, Any] = {}
        if payload_raw is not None:
            payload_str = _b2s(payload_raw)
            if isinstance(payload_str, str):
                try:
                    obj = json.loads(payload_str)
                    if isinstance(obj, dict):
                        payload = obj
                    else:
                        # If it's not a dict (e.g., list), wrap it
                        payload = {"_payload": obj}
                except json.JSONDecodeError:
                    # Keep the raw string if malformed
                    payload = {"_payload_raw": payload_str}

        scored.append(
            ScoredResult(
                id=result_id,
                payload=payload,
                score=score,
            )
        )

    return scored


# -------------------------- Valkey Adapter (GLIDE) ----------------------------

class ValkeyAdapter(VectorDBInterface):
    def __init__(
            self,
            url: str | None,
            api_key: str | None = None,
            embedding_engine: EmbeddingEngine | None = None
    ) -> None:
        if not embedding_engine:
            raise ValkeyVectorEngineInitializationError(
                "Embedding engine is required. Provide 'embedding_engine' to the Valkey adapter."
            )

        self._host, self._port = parse_host_port(url)
        self._api_key = api_key
        self._embedding_engine = embedding_engine
        self._client: GlideClient | None = None
        self._connected = False
        self.VECTOR_DB_LOCK = asyncio.Lock()

    # -------------------- lifecycle --------------------

    async def get_connection(self) -> GlideClient:
        if self._connected and self._client is not None:
            return self._client

        cfg = GlideClientConfiguration(
            [NodeAddress(self._host, self._port)],
            use_tls=False,
            request_timeout=5000,
            reconnect_strategy=BackoffStrategy(num_of_retries=3, factor=1000, exponent_base=2)
        )
        self._client = await GlideClient.create(cfg)
        self._connected = True

        return self._client

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
        self._client = None
        self._connected = False

    # -------------------- helpers --------------------

    def _index_name(self, collection: str) -> str:
        return f"index:{collection}"

    def _key_prefix(self, collection: str) -> str:
        return f"vdb:{collection}:"

    def _key(self, collection: str, pid: str) -> str:
        return f"{self._key_prefix(collection)}{pid}"

    def _ensure_dims(self) -> int:
        dims = self._embedding_engine.get_dimensions()
        return int(dims)

    # -------------------- VectorDBInterface methods --------------------

    async def has_collection(self, collection_name: str) -> bool:
        client = await self.get_connection()
        try:
            await ft.info(client, self._index_name(collection_name))
            return True
        except Exception:
            return False

    async def create_collection(
            self,
            collection_name: str,
            payload_schema: Any | None = None,
    ) -> None:
        async with self.VECTOR_DB_LOCK:
            try:
                if await self.has_collection(collection_name):
                    logger.info(f"Collection {collection_name} already exists")
                    return

                fields = [
                    TagField("id"),
                    VectorField(
                        name="vector",
                        algorithm=VectorAlgorithm.HNSW,
                        attributes=VectorFieldAttributesHnsw(
                            dimensions=self._embedding_engine.get_vector_size(),
                            distance_metric=DistanceMetricType.COSINE,
                            type=VectorType.FLOAT32
                        )
                    )
                ]
                prefixes = [self._key_prefix(collection_name)]
                options = FtCreateOptions(DataType.JSON, prefixes)
                index = self._index_name(collection_name)

                ok = await ft.create(self._client, index, fields, options)
                if ok not in (b"OK", "OK"):
                    raise Exception(f"FT.CREATE failed for index '{index}': {ok!r}")

            except Exception as e:
                logger.error(f"Error creating collection {collection_name}: {str(e)}")
                raise e

    async def create_data_points(
            self,
            collection_name: str,
            data_points: list[DataPoint],
    ) -> None:
        client = await self.get_connection()
        assert self._client is not None

        try:
            if not await self.has_collection(collection_name):
                raise CollectionNotFoundError(f"Collection {collection_name} not found!")

            # Embed the data points
            data_to_embed = [DataPoint.get_embeddable_data(data_point) for data_point in data_points]
            data_vectors = await self.embed_data(data_to_embed)

            documents = []
            for data_point, embedding in zip(data_points, data_vectors):
                payload = serialize_for_json(data_point.model_dump())

                doc_data = {
                    "id": str(data_point.id),
                    "vector": embedding,
                    "payload_data": json.dumps(payload),  # Store as JSON string
                }

                documents.append(glide_json.set(
                    client,
                    self._key(collection_name, str(data_point.id)),
                    "$",
                    json.dumps(doc_data),
                ))

            await asyncio.gather(*documents)

        except RequestError as e:
            # Helpful guidance if JSON vector arrays aren't supported by the deployed module
            logger.error(f"JSON.SET failed: {e}")
            raise e

        except Exception as e:
            logger.error(f"Error creating data points: {str(e)}")
            raise e

    async def retrieve(
            self,
            collection_name: str,
            data_point_ids: list[str],
    ) -> list[dict[str, Any]]:
        client = await self.get_connection()
        assert self._client is not None

        try:
            results = []
            for data_id in data_point_ids:
                key = self._key(collection_name, data_id)
                raw_doc = await glide_json.get(client, key, "$")
                if raw_doc:
                    doc = json.loads(raw_doc)
                    payload_str = doc[0]["payload_data"]
                    try:
                        payload = json.loads(payload_str)
                        results.append(payload)
                    except json.JSONDecodeError:
                        # Fallback to the document itself if payload parsing fails
                        results.append(raw_doc)

            return results

        except Exception as e:
            logger.error(f"Error retrieving data points: {str(e)}")
            return []

    async def search(
            self,
            collection_name: str,
            query_text: str | None = None,
            query_vector: list[float] | None = None,
            limit: int | None = 15,
            with_vector: bool = False,
    ) -> list[ScoredResult]:
        client = await self.get_connection()
        assert self._client is not None

        if query_text is None and query_vector is None:
            raise MissingQueryParameterError()

        if not await self.has_collection(collection_name):
            logger.warning(
                f"Collection '{collection_name}' not found in ValkeyAdapter.search; returning []."
            )
            return []

        if limit is None:
            info = await ft.info(client, self._index_name(collection_name))
            limit = info["num_docs"]

        if limit <= 0:
            return []

        try:
            # Get the query vector
            if query_vector is None:
                [vec] = await self.embed_data([query_text])
            else:
                vec = query_vector
            vec_bytes = _to_float32_bytes(vec)

            # Set return fields
            return_fields = [
                ReturnField("$.id", alias="id"),
                ReturnField("$.payload_data", alias="payload_data"),
                ReturnField("__vector_score", alias="score")
            ]
            if with_vector:
                return_fields.append(ReturnField("$.vector", alias="vector"))

            vector_param_name = "query_vector"
            query = f"*=>[KNN {limit} @vector ${vector_param_name}]"
            query_options = FtSearchOptions(
                params={vector_param_name: vec_bytes},
                return_fields=return_fields
            )

            # Execute the search
            raw_results = await ft.search(
                client=client,
                index_name=self._index_name(collection_name),
                query=query,
                options=query_options
            )

            scored_results = build_scored_results_from_ft(raw_results)
            return scored_results

        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise e

    async def batch_search(
            self,
            collection_name: str,
            query_texts: list[str],
            limit: int | None,
            with_vectors: bool = False,
    ) -> list[list[ScoredResult]]:
        # Embed all queries at once
        vectors = await self.embed_data(query_texts)

        # Execute searches in parallel
        search_tasks = [
            self.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=limit,
                with_vector=with_vectors,
            )
            for vector in vectors
        ]

        # Filter results by score threshold
        results = await asyncio.gather(*search_tasks)
        return [
            [result for result in result_group if result.score < 0.1] for result_group in results
        ]

    async def delete_data_points(
            self,
            collection_name: str,
            data_point_ids: list[str],
    ) -> dict[str, int]:
        client = await self.get_connection()
        assert self._client is not None

        ids = [self._key(collection_name, id) for id in data_point_ids]

        try:
            deleted_count = await client.delete(ids)
            logger.info(f"Deleted {deleted_count} data points from collection {collection_name}")
            return {"deleted": deleted_count}
        except Exception as e:
            logger.error(f"Error deleting data points: {str(e)}")
            raise e

    async def prune(self):
        client = await self.get_connection()
        assert self._client is not None
        try:
            all_indexes = await ft.list(client)
            for index in all_indexes:
                await ft.dropindex(client, index)
                logger.info(f"Dropped index {index}")

        except Exception as e:
            logger.error(f"Error during prune: {str(e)}")
            raise e

    async def embed_data(self, data: list[str]) -> list[list[float]]:
        return await self._embedding_engine.embed_text(data)
