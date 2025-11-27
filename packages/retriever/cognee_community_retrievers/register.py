from cognee.modules.retrieval.base_retriever import BaseRetriever
from cognee.modules.retrieval.register_retriever import register_retriever
from cognee.modules.search.types import SearchType


def register(search_type: SearchType, retriever: BaseRetriever):
    register_retriever(search_type, retriever)
