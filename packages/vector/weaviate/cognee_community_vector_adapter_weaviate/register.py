from cognee.infrastructure.databases.vector import use_vector_adapter

from .weaviate_adapter import WeaviateAdapter

use_vector_adapter("weaviate", WeaviateAdapter) 