from typing import Any

from loguru import logger
from pymilvus import AnnSearchRequest, MilvusClient, RRFRanker

from engines.contracts.config import get_settings
from engines.insight_agent.tools.utils import to_datetime
from engines.insight_agent.tools.vector_search.embedder import (
    BgeM3Embedder,
    VectorEmbedding,
)
from engines.insight_agent.tools.vector_search.schemas import (
    OUTPUT_FIELDS,
    build_collection_schema,
    build_index_params,
)
from engines.insight_agent.tools.vector_search.search_results import (
    SearchHit,
    VectorDocument,
)


class VectorSearchRepository:
    """Milvus 仓储,执行双通道检索与持久化。"""

    def __init__(self) -> None:
        """绑定 Milvus 集合名与向量化器并延迟连接。"""
        self.collection_name = get_settings().MILVUS_INSIGHT_COLLECTION
        self.embedder = BgeM3Embedder(
            model_name=get_settings().INSIGHT_EMBEDDING_MODEL,
            device=get_settings().INSIGHT_EMBEDDING_DEVICE,
        )
        self._client = None

    @property
    def client(self):
        """懒加载 Milvus 客户端单例。"""
        if self._client is None:
            settings = get_settings()
            kwargs: dict[str, Any] = {
                "uri": settings.MILVUS_URI,
                "db_name": settings.MILVUS_DB_NAME,
            }
            self._client = MilvusClient(**kwargs)
        return self._client

    def ensure_collection(self, drop_existing: bool = False) -> None:
        """确保 Milvus 集合存在，支持可选的强行删除重建。"""
        if drop_existing and self.client.has_collection(self.collection_name):
            self.client.drop_collection(self.collection_name)
        if self.client.has_collection(self.collection_name):
            return
        schema = build_collection_schema(self.client, get_settings().INSIGHT_DENSE_DIM)
        index_params = build_index_params(self.client)
        self.client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params,
        )
        logger.info(f"创建Milvus集合 {self.collection_name}")

    def upsert_documents(self, documents: list[VectorDocument]) -> int:
        """双通道向量化文档并写入 Milvus 集合。"""
        if not documents:
            return 0
        self.ensure_collection()
        embeddings = self.embedder.encode_documents([doc.content for doc in documents])
        entities = [
            doc.to_milvus_record(
                dense_vector=embedding.dense_vector,
                sparse_vector=embedding.sparse_vector,
            )
            for doc, embedding in zip(documents, embeddings)
            if embedding.dense_vector and embedding.sparse_vector
        ]
        if not entities:
            return 0
        self.client.upsert(collection_name=self.collection_name, data=entities)
        logger.info(f"成功插入Milvus集合数据:{len(entities)}")
        return len(entities)

    def search(self, query: str, limit: int, filter_expr: str | None = None) -> list[SearchHit]:
        """根据查询文本进行多路归并混合检索。"""
        self.ensure_collection()
        query_embedding = self.embedder.encode_query(query)
        if not query_embedding:
            return []
        return self._hybrid_search(query_embedding, limit, filter_expr)

    def _hybrid_search(
            self,
            query_embedding: VectorEmbedding,
            limit: int,
            filter_expr: str | None = None,
    ) -> list[SearchHit]:
        """稠密稀疏双路召回经 RRF 融合排序。"""
        request_filter = {"expr": filter_expr} if filter_expr else {}
        dense_request = AnnSearchRequest(
            data=[query_embedding.dense_vector],
            anns_field="dense_vector",
            param={"metric_type": "COSINE"},
            limit=limit,
            **request_filter,
        )
        sparse_request = AnnSearchRequest(
            data=[query_embedding.sparse_vector],
            anns_field="sparse_vector",
            param={"metric_type": "IP"},
            limit=limit,
            **request_filter,
        )
        result = self.client.hybrid_search(
            collection_name=self.collection_name,
            reqs=[dense_request, sparse_request],
            ranker=RRFRanker(),
            limit=limit,
            output_fields=OUTPUT_FIELDS,
        )
        return self._map_hits(result, "semantic_recall")

    @staticmethod
    def _map_hits(raw_result: Any, channel: str) -> list[SearchHit]:
        """将 Milvus 命中原始结果映射为 SearchHit。"""
        if not raw_result:
            return []
        first_query_hits = raw_result[0]
        hits: list[SearchHit] = []
        for hit_dict in first_query_hits:
            entity = hit_dict.get("entity")
            hits.append(
                SearchHit(
                    retrieval_score=hit_dict.get("distance"),
                    retrieval_channel=channel,
                    retrieval_doc=VectorDocument(
                        doc_id=hit_dict.get("doc_id"),
                        platform=entity.get("platform"),
                        source_table=entity.get("source_table"),
                        mysql_pk=entity.get("mysql_pk"),
                        content=entity.get("content"),
                        published_at=to_datetime(entity.get("published_at")),
                        source_keyword=entity.get("source_keyword"),
                        likes=entity.get("likes"),
                        comments=entity.get("comments"),
                        shares=entity.get("share"),
                        collects=entity.get("collects"),
                        replies=entity.get("replies"),
                        hotness_score=entity.get("hotness_score"),
                    ),
                )
            )
        return hits
