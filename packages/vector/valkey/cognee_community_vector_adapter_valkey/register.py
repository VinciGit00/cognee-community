from cognee.infrastructure.databases.vector import use_vector_adapter

from .valkey_adapter import ValkeyAdapter

use_vector_adapter("valkey", ValkeyAdapter)
