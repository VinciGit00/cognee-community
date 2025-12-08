from cognee.modules.retrieval.register_retriever import use_retriever
from cognee.modules.search.types import SearchType

from cognee_community_retriever_code.code_retriever import CodeRetriever, CodeSearchType

use_retriever(SearchType[CodeSearchType.name], CodeRetriever)
