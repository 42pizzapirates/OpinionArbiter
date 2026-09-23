from loguru import logger

from engines.insight_agent.tools.vector_search.repository import VectorSearchRepository
from engines.insight_agent.tools.vector_search.source.reader import SourceDocumentReader


async def sync_data(drop_existing: bool = True) -> int:
    """全量同步 MySQL 文档到 Milvus 知识库。"""
    milvus_repository = VectorSearchRepository()
    source_reader = SourceDocumentReader()
    milvus_repository.ensure_collection(drop_existing=drop_existing)
    all_docs = await source_reader.get_all_documents()
    count = milvus_repository.upsert_documents(all_docs)
    logger.info(f"Milvus 同步完成 总计={count}")
    return count
