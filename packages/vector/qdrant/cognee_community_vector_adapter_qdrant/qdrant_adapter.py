import asyncio

from cognee.infrastructure.databases.exceptions import MissingQueryParameterError
from cognee.infrastructure.databases.vector import VectorDBInterface
from cognee.infrastructure.databases.vector.embeddings.EmbeddingEngine import (
    EmbeddingEngine,
)
from cognee.infrastructure.databases.vector.exceptions import CollectionNotFoundError
from cognee.infrastructure.databases.vector.models.ScoredResult import ScoredResult
from cognee.infrastructure.engine import DataPoint
from cognee.infrastructure.engine.utils import parse_id
from cognee.shared.logging_utils import get_logger
from qdrant_client import AsyncQdrantClient, models

logger = get_logger("QDrantAdapter")


class IndexSchema(DataPoint):
    text: str

    metadata: dict = {"index_fields": ["text"]}


def create_hnsw_config(hnsw_config: dict):
    if hnsw_config is not None:
        return models.HnswConfig()
    return None


def create_optimizers_config(optimizers_config: dict):
    if optimizers_config is not None:
        return models.OptimizersConfig()
    return None


def create_quantization_config(quantization_config: dict):
    if quantization_config is not None:
        return models.QuantizationConfig()
    return None


class QDrantAdapter(VectorDBInterface):
    name = "Qdrant"
    url: str = None
    api_key: str = None
    qdrant_path: str = None

    def __init__(self, url, api_key, embedding_engine: EmbeddingEngine, qdrant_path=None):
        self.embedding_engine = embedding_engine

        if qdrant_path is not None:
            self.qdrant_path = qdrant_path
        else:
            self.url = url
            self.api_key = api_key
        self.VECTOR_DB_LOCK = asyncio.Lock()

    def get_qdrant_client(self) -> AsyncQdrantClient:
        if self.qdrant_path is not None:
            return AsyncQdrantClient(path=self.qdrant_path, port=6333)
        elif self.url is not None:
            return AsyncQdrantClient(url=self.url, api_key=self.api_key, port=6333)

        return AsyncQdrantClient(location=":memory:")

    async def embed_data(self, data: list[str]) -> list[float]:
        return await self.embedding_engine.embed_text(data)

    async def has_collection(self, collection_name: str) -> bool:
        client = self.get_qdrant_client()
        result = await client.collection_exists(collection_name)
        await client.close()
        return result

    async def create_collection(
        self,
        collection_name: str,
        payload_schema=None,
    ):
        async with self.VECTOR_DB_LOCK:
            client = self.get_qdrant_client()

            if not await client.collection_exists(collection_name):
                await client.create_collection(
                    collection_name=collection_name,
                    vectors_config={
                        "text": models.VectorParams(
                            size=self.embedding_engine.get_vector_size(),
                            distance="Cosine",
                        )
                    },
                )

            await client.close()

    async def create_data_points(self, collection_name: str, data_points: list[DataPoint]):
        from qdrant_client.http.exceptions import UnexpectedResponse

        client = self.get_qdrant_client()

        data_vectors = await self.embed_data(
            [DataPoint.get_embeddable_data(data_point) for data_point in data_points]
        )

        def convert_to_qdrant_point(data_point: DataPoint):
            return models.PointStruct(
                id=str(data_point.id),
                payload=data_point.model_dump(),
                vector={"text": data_vectors[data_points.index(data_point)]},
            )

        points = [convert_to_qdrant_point(point) for point in data_points]

        try:
            # Use upsert for AsyncQdrantClient (upload_points doesn't exist or is sync)
            await client.upsert(collection_name=collection_name, points=points)
        except UnexpectedResponse as error:
            if "Collection not found" in str(error):
                raise CollectionNotFoundError(
                    message=f"Collection {collection_name} not found!"
                ) from error
            else:
                raise error
        except Exception as error:
            logger.error("Error uploading data points to Qdrant: %s", str(error))
            raise error
        finally:
            await client.close()

    async def create_vector_index(self, index_name: str, index_property_name: str):
        await self.create_collection(f"{index_name}_{index_property_name}")

    async def index_data_points(
        self, index_name: str, index_property_name: str, data_points: list[DataPoint]
    ):
        await self.create_data_points(
            f"{index_name}_{index_property_name}",
            [
                IndexSchema(
                    id=data_point.id,
                    text=getattr(data_point, data_point.metadata["index_fields"][0]),
                )
                for data_point in data_points
            ],
        )

    async def retrieve(self, collection_name: str, data_point_ids: list[str]):
        client = self.get_qdrant_client()
        results = await client.retrieve(collection_name, data_point_ids, with_payload=True)
        await client.close()
        return results

    async def search(
        self,
        collection_name: str,
        query_text: str | None = None,
        query_vector: list[float] | None = None,
        limit: int | None = 15,
        with_vector: bool = False,
    ) -> list[ScoredResult]:
        if query_text is None and query_vector is None:
            raise MissingQueryParameterError()

        if not await self.has_collection(collection_name):
            return []

        if query_vector is None:
            query_vector = (await self.embed_data([query_text]))[0]

        client = None
        try:
            client = self.get_qdrant_client()
            if limit is None:
                collection_size = await client.count(collection_name=collection_name)
                limit = collection_size.count
            if limit == 0:
                await client.close()
                return []

            # Use query_points instead of search (API change in qdrant-client)
            # query_points is the correct method for AsyncQdrantClient
            query_result = await client.query_points(
                collection_name=collection_name,
                query=query_vector,
                using="text",
                limit=limit,
                with_vectors=with_vector,
            )

            await client.close()

            # Extract points from query_result
            results = query_result.points

            return [
                ScoredResult(
                    id=parse_id(str(result.id)),
                    payload={
                        **result.payload,
                        "id": parse_id(str(result.id)),
                    },
                    score=1 - result.score if hasattr(result, 'score') else 1.0,
                )
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error in Qdrant search: {e}", exc_info=True)
            if client:
                await client.close()
            return []

    async def batch_search(
        self,
        collection_name: str,
        query_texts: list[str],
        limit: int | None = None,
        with_vectors: bool = False,
    ):
        """
        Perform batch search in a Qdrant collection with dynamic search requests.

        Args:
        - collection_name (str): Name of the collection to search in.
        - query_texts (List[str]): List of query texts to search for.
        - limit (int): List of result limits for search requests.
        - with_vectors (bool, optional): Bool indicating whether to return
                                         vectors for search requests.

        Returns:
        - results: The search results from Qdrant.
        """

        client = self.get_qdrant_client()
        if limit is None:
            collection_size = await client.count(collection_name=collection_name)
            limit = collection_size.count
        if limit == 0:
            await client.close()
            return []

        client = self.get_qdrant_client()

        try:
            # Use query_batch instead of search_batch (API change in qdrant-client)
            # query_batch is the correct method for AsyncQdrantClient
            query_results = await client.query_batch(
                collection_name=collection_name,
                query_texts=query_texts,
                limit=limit,
                with_vectors=with_vectors,
            )

            await client.close()

            # Extract points from each query result and filter by score
            filtered_results = []
            for query_result in query_results:
                points = query_result.points if hasattr(query_result, 'points') else []
                filtered_points = [
                    result for result in points
                    if hasattr(result, 'score') and result.score > 0.9
                ]
                filtered_results.append(filtered_points)

            return filtered_results
        except Exception as e:
            logger.error(f"Error in Qdrant batch_search: {e}", exc_info=True)
            await client.close()
            return []

    async def delete_data_points(self, collection_name: str, data_point_ids: list[str]):
        client = self.get_qdrant_client()
        results = await client.delete(collection_name, data_point_ids)
        return results

    async def prune(self):
        client = self.get_qdrant_client()

        response = await client.get_collections()

        for collection in response.collections:
            await client.delete_collection(collection.name)

        await client.close()

    async def get_collection_names(self) -> list[str]:
        """
        Get names of all collections in the database.

        Returns:
            list[str]: List of collection names.
        """

        client = self.get_qdrant_client()

        response = await client.get_collections()

        result = [collection.name for collection in response.collections]

        await client.close()

        return result
