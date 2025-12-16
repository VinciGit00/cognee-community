from cognee.infrastructure.databases.dataset_database_handler import use_dataset_database_handler
from cognee.infrastructure.databases.vector import use_vector_adapter

from .qdrant_adapter import QDrantAdapter
from .QdrantDatasetDatabaseHandler import QdrantDatasetDatabaseHandler

use_vector_adapter("qdrant", QDrantAdapter)
use_dataset_database_handler("qdrant", QdrantDatasetDatabaseHandler, "qdrant")
