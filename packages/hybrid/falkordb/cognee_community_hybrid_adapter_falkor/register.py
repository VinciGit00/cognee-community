from cognee.infrastructure.databases.dataset_database_handler import use_dataset_database_handler
from cognee.infrastructure.databases.graph import use_graph_adapter
from cognee.infrastructure.databases.vector import use_vector_adapter

from .falkor_adapter import FalkorDBAdapter
from .FalkorDatasetDatabaseHandlerGraph import FalkorDatasetDatabaseHandlerGraph
from .FalkorDatasetDatabaseHandlerVector import FalkorDatasetDatabaseHandlerVector

use_vector_adapter("falkor", FalkorDBAdapter)
use_graph_adapter("falkor", FalkorDBAdapter)
use_dataset_database_handler("falkor_graph", FalkorDatasetDatabaseHandlerGraph, "falkor")
use_dataset_database_handler("falkor_vector", FalkorDatasetDatabaseHandlerVector, "falkor")
