import os
import tempfile
from typing import List, Dict, Optional, Any
from uuid import UUID

from cognee.infrastructure.databases.vector.vector_db_interface import VectorDBInterface
from cognee.infrastructure.databases.vector.embeddings.EmbeddingEngine import EmbeddingEngine
from cognee.infrastructure.engine import DataPoint
from cognee.shared.logging_utils import get_logger
from cognee.infrastructure.files.storage import get_file_storage

logger = get_logger("MilvusAdapter")


class MilvusAdapter(VectorDBInterface):
    """
    Interface for interacting with a Milvus vector database.

    This adapter provides methods for managing collections, creating data points,
    searching, and other vector database operations using Milvus.

    Public methods:
    - get_milvus_client
    - embed_data
    - has_collection
    - create_collection
    - create_data_points
    - create_vector_index
    - index_data_points
    - retrieve
    - search
    - batch_search
    - delete_data_points
    - prune
    """

    name = "Milvus"

    def __init__(self, url: str, api_key: Optional[str], embedding_engine: EmbeddingEngine):
        self.url = url
        self.api_key = api_key
        self.embedding_engine = embedding_engine

    def get_milvus_client(self):
        """
        Retrieve a Milvus client instance.

        Returns a MilvusClient object configured with the provided URL and optional API key.

        Returns:
        --------
            A MilvusClient instance.
        """
        from pymilvus import MilvusClient

        # Ensure the parent directory exists for local file-based Milvus databases
        if not self.url.startswith("http"):
            # Local file path
            db_dir = os.path.dirname(self.url)
            if db_dir:
                file_storage = get_file_storage(db_dir)
                # This is a sync operation, but we'll handle it appropriately
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(file_storage.ensure_directory_exists())
                except RuntimeError:
                    # If no event loop is running, create a temporary one
                    import asyncio
                    asyncio.run(file_storage.ensure_directory_exists())

        if self.api_key:
            client = MilvusClient(uri=self.url, token=self.api_key)
        else:
            client = MilvusClient(uri=self.url)

        return client

    async def embed_data(self, data: List[str]) -> List[List[float]]:
        """
        Embed text data into vectors using the embedding engine.

        Parameters:
        -----------
            data (List[str]): List of text strings to embed.

        Returns:
        --------
            List[List[float]]: List of embedding vectors.
        """
        return await self.embedding_engine.embed_text(data)

    def has_collection(self, collection_name: str) -> bool:
        """
        Check if a collection exists in the Milvus database.

        Parameters:
        -----------
            collection_name (str): Name of the collection to check.

        Returns:
        --------
            bool: True if collection exists, False otherwise.
        """
        client = self.get_milvus_client()
        return client.has_collection(collection_name)

    async def create_collection(self, collection_name: str, payload_schema=None):
        """
        Create a new collection in the Milvus database.

        Parameters:
        -----------
            collection_name (str): Name of the collection to create.
            payload_schema: Optional schema definition for the collection.

        Raises:
        -------
            MilvusException if there are issues creating the collection.
        """
        from pymilvus import DataType, MilvusException

        client = self.get_milvus_client()
        
        vector_size = self.embedding_engine.get_vector_size()
        
        schema = {
            "fields": [
                {"name": "id", "type": DataType.VARCHAR, "max_length": 255, "is_primary": True},
                {"name": "vector", "type": DataType.FLOAT_VECTOR, "dim": vector_size},
                {"name": "payload", "type": DataType.JSON},
            ]
        }

        try:
            if not self.has_collection(collection_name):
                client.create_collection(
                    collection_name=collection_name,
                    schema=schema,
                    metric_type="IP",  # Inner Product
                    consistency_level="Strong"
                )
        except MilvusException as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            raise

    async def create_data_points(self, collection_name: str, data_points: List[DataPoint]):
        """
        Create data points in a Milvus collection.

        Parameters:
        -----------
            collection_name (str): Name of the collection.
            data_points (List[DataPoint]): List of data points to insert.
        """
        from pymilvus import MilvusException, exceptions

        client = self.get_milvus_client()

        if not self.has_collection(collection_name):
            await self.create_collection(collection_name)

        # Prepare data for insertion
        data_vectors = await self.embed_data(
            [DataPoint.get_embeddable_data(data_point) for data_point in data_points]
        )

        records = []
        for data_point, vector in zip(data_points, data_vectors):
            records.append({
                "id": str(data_point.id),
                "vector": vector,
                "payload": data_point.to_dict()
            })

        try:
            client.insert(collection_name=collection_name, data=records)
        except MilvusException as e:
            logger.error(f"Error inserting data points: {e}")
            raise

    async def create_vector_index(self, collection_name: str, field_name: str = "vector"):
        """
        Create a vector index on a collection.

        Parameters:
        -----------
            collection_name (str): Name of the collection.
            field_name (str): Name of the vector field to index.
        """
        from pymilvus import MilvusException, exceptions

        client = self.get_milvus_client()

        index_params = {
            "metric_type": "IP",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }

        try:
            client.create_index(
                collection_name=collection_name,
                field_name=field_name,
                index_params=index_params
            )
        except MilvusException as e:
            logger.error(f"Error creating index: {e}")
            raise

    async def index_data_points(self, collection_name: str, data_points: List[DataPoint]):
        """
        Index data points in the collection.

        Parameters:
        -----------
            collection_name (str): Name of the collection.
            data_points (List[DataPoint]): List of data points to index.
        """
        await self.create_data_points(collection_name, data_points)
        await self.create_vector_index(collection_name)

    async def retrieve(
        self, collection_name: str, data_point_ids: List[str]
    ) -> List[DataPoint]:
        """
        Retrieve data points by their IDs.

        Parameters:
        -----------
            collection_name (str): Name of the collection.
            data_point_ids (List[str]): List of data point IDs to retrieve.

        Returns:
        --------
            List[DataPoint]: List of retrieved data points.
        """
        client = self.get_milvus_client()
        
        if not self.has_collection(collection_name):
            return []

        try:
            results = client.get(
                collection_name=collection_name,
                ids=data_point_ids
            )
            
            data_points = []
            for result in results:
                payload = result.get("payload", {})
                data_point = DataPoint(**payload)
                data_points.append(data_point)
            
            return data_points
        except Exception as e:
            logger.error(f"Error retrieving data points: {e}")
            return []

    async def search(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 10,
        with_vector: bool = False,
        **kwargs
    ) -> List[Dict]:
        """
        Search for similar vectors in the collection.

        Parameters:
        -----------
            collection_name (str): Name of the collection to search.
            query_text (str): Query text to search for.
            limit (int): Maximum number of results to return.
            with_vector (bool): Whether to include vectors in results.

        Returns:
        --------
            List[Dict]: List of search results.
        """
        from pymilvus import MilvusException, exceptions

        client = self.get_milvus_client()

        if not self.has_collection(collection_name):
            logger.warning(
                f"Collection '{collection_name}' not found in MilvusAdapter.search; returning []."
            )
            return []

        # Generate query vector
        query_vectors = await self.embed_data([query_text])
        
        search_params = {
            "metric_type": "IP",
            "params": {"nprobe": 10}
        }

        try:
            results = client.search(
                collection_name=collection_name,
                data=query_vectors,
                limit=limit,
                search_params=search_params,
                output_fields=["id", "payload"]
            )
            
            formatted_results = []
            for result in results[0]:  # results is a list of lists
                formatted_results.append({
                    "id": result["id"],
                    "score": result["distance"],
                    "payload": result["entity"].get("payload", {})
                })
            
            return formatted_results
        except MilvusException as e:
            logger.error(f"Error searching collection {collection_name}: {e}")
            return []

    async def batch_search(
        self,
        collection_name: str,
        query_texts: List[str],
        limit: int = 10,
        **kwargs
    ) -> List[List[Dict]]:
        """
        Perform batch search operations.

        Parameters:
        -----------
            collection_name (str): Name of the collection to search.
            query_texts (List[str]): List of query texts.
            limit (int): Maximum number of results per query.

        Returns:
        --------
            List[List[Dict]]: List of search results for each query.
        """
        results = []
        for query_text in query_texts:
            result = await self.search(collection_name, query_text, limit, **kwargs)
            results.append(result)
        return results

    async def delete_data_points(self, collection_name: str, data_point_ids: List[str]):
        """
        Delete data points from a collection.

        Parameters:
        -----------
            collection_name (str): Name of the collection.
            data_point_ids (List[str]): List of data point IDs to delete.
        """
        client = self.get_milvus_client()
        
        if not self.has_collection(collection_name):
            return

        try:
            client.delete(
                collection_name=collection_name,
                ids=data_point_ids
            )
        except Exception as e:
            logger.error(f"Error deleting data points: {e}")

    async def prune(self):
        """
        Remove all collections and data from the Milvus database.
        """
        client = self.get_milvus_client()
        
        try:
            collections = client.list_collections()
            for collection in collections:
                client.drop_collection(collection_name=collection)
        except Exception as e:
            logger.error(f"Error pruning Milvus database: {e}")

    async def get_distance_from_collection_elements(
        self, collection_name: str, elements: List[DataPoint]
    ) -> List[float]:
        """
        Get distances from collection elements.

        Parameters:
        -----------
            collection_name (str): Name of the collection.
            elements (List[DataPoint]): List of data points to get distances for.

        Returns:
        --------
            List[float]: List of distances.
        """
        if not elements:
            return []

        # For Milvus, we'll return similarity scores by searching for each element
        distances = []
        for element in elements:
            embeddable_data = DataPoint.get_embeddable_data(element)
            results = await self.search(collection_name, embeddable_data, limit=1)
            
            if results:
                # Milvus returns similarity scores (higher is better)
                # Convert to distance (lower is better) by subtracting from 1
                distance = 1.0 - results[0]["score"]
                distances.append(distance)
            else:
                distances.append(float('inf'))  # Max distance if not found
        
        return distances 