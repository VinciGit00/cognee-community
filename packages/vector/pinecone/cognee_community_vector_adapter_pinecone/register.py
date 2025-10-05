from cognee.infrastructure.databases.vector import use_vector_adapter

from .pinecone_adapter import PineconeAdapter

use_vector_adapter("pinecone", PineconeAdapter)
