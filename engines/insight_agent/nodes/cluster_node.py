from collections import defaultdict
from functools import lru_cache
from typing import Any

import numpy as np

from engines.common.nodes.base_node import BaseNode, ResearchNodeContext
from engines.contracts.config import get_settings
from engines.contracts.dimensions import dimension_for_key, get_insight_cluster_rules
from engines.insight_agent.evidence_processor import EvidenceCluster, EvidenceRecord
from engines.insight_agent.state import InsightState


@lru_cache(maxsize=1)
def _get_embedding_model():
    """惰性加载 BGE-M3 聚类嵌入模型。"""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(str(get_settings().INSIGHT_CLUSTER_MODEL))


@lru_cache(maxsize=1)
def _get_dimension_vector():
    """缓存五维关键词的归一化向量供路由匹配。"""
    rules = get_insight_cluster_rules()
    dimension_texts = [
        f"{dimension_for_key(dim_key).title}: {' '.join(keywords)}"
        for dim_key, keywords in rules.items()
    ]
    dimension_keys = list(rules.keys())
    dimension_embeddings = _get_embedding_model().encode(
        dimension_texts, normalize_embeddings=True, show_progress_bar=False
    )
    return dimension_keys, dimension_embeddings


class ClusterNode(BaseNode):
    """证据聚类节点：按语义或规则归入私域五维。"""

    def __init__(self, context: ResearchNodeContext) -> None:
        """初始化聚类节点上下文。"""
        super().__init__(context)

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        """对证据池记录执行聚类并回写聚类结果。"""
        pool = state["evidence_pool"]
        pool.clusters = self._cluster_evidence(pool.records)
        return {"evidence_pool": pool}

    def _cluster_evidence(self, records: list[EvidenceRecord]) -> list[EvidenceCluster]:
        """按配置选择语义或规则聚类策略。"""
        if self._is_semantic_enabled(records):
            return self._cluster_by_semantics(records)
        return self._cluster_by_rules(records)

    def _is_semantic_enabled(self, records: list[EvidenceRecord]) -> bool:
        """判断是否满足语义聚类开关与最小样本量。"""
        settings = get_settings()
        return (
                settings.INSIGHT_CLUSTERING_ENABLED
                and bool(settings.INSIGHT_CLUSTER_MODEL)
                and len(records) >= settings.INSIGHT_CLUSTER_MIN_CLUSTER_SIZE
        )

    def _cluster_by_rules(self, records: list[EvidenceRecord]) -> list[EvidenceCluster]:
        """按五维关键词规则将证据归入维度簇。"""
        cluster_data: dict[str, list[EvidenceRecord]] = defaultdict(list)
        for record in records:
            cluster_id = self._match_rule_key(record)
            record.cluster_id = cluster_id
            cluster_data[cluster_id].append(record)
        return self._assemble_clusters(cluster_data)

    def _match_rule_key(self, record: EvidenceRecord) -> str:
        """按关键词命中匹配证据所属私域维度键。"""
        text = f"{record.source_keyword} {record.content}"
        for dim_key, keywords in get_insight_cluster_rules().items():
            if any(k in text for k in keywords):
                return f"cluster_{dim_key}"
        return "cluster_other"

    def _cluster_by_semantics(self, records: list[EvidenceRecord]) -> list[EvidenceCluster]:
        """BGE-M3 编码后 KMeans 聚类再路由到维度。"""
        settings = get_settings()
        sampled = records[: settings.INSIGHT_CLUSTER_MAX_RECORDS]
        contents = [f"{r.source_keyword} {r.content}".strip() for r in sampled]
        embeddings = _get_embedding_model().encode(
            contents, normalize_embeddings=True, show_progress_bar=False
        )
        assignments = self._calculate_kmeans_labels(embeddings, len(sampled))
        temp_groups: dict[int, list[EvidenceRecord]] = defaultdict(list)
        for record, label in zip(sampled, assignments):
            temp_groups[label].append(record)
        cluster_data: dict[str, list[EvidenceRecord]] = defaultdict(list)
        for cluster_records in temp_groups.values():
            dim_key = self._route_to_dimension(cluster_records)
            cluster_id = f"cluster_{dim_key}"
            for record in cluster_records:
                record.cluster_id = cluster_id
                cluster_data[cluster_id].append(record)
        return self._assemble_clusters(cluster_data)

    def _calculate_kmeans_labels(self, embeddings: Any, count: int) -> list[int]:
        """对嵌入执行 KMeans 并返回簇标签。"""
        from sklearn.cluster import KMeans

        k = self._determine_optimal_k(count)
        return [
            int(l)
            for l in KMeans(n_clusters=k, n_init="auto", random_state=42).fit_predict(embeddings)
        ]

    def _determine_optimal_k(self, count: int) -> int:
        """按样本量与配置上下界确定最优簇数。"""
        settings = get_settings()
        k = count // settings.INSIGHT_CLUSTER_MIN_CLUSTER_SIZE
        return max(2, min(settings.INSIGHT_CLUSTER_MAX_CLUSTERS, k, count))

    def _route_to_dimension(self, records: list[EvidenceRecord]) -> str:
        """用 BGE-M3 向量相似度将簇匹配到私域维度。"""
        sample = " ".join(r.content[:30] for r in records[:10])
        emb = _get_embedding_model().encode(
            [sample], normalize_embeddings=True, show_progress_bar=False
        )
        keys, dimension_embs = _get_dimension_vector()
        similarities = np.dot(emb, dimension_embs.T)[0]
        return keys[int(np.argmax(similarities))]

    def _assemble_clusters(self, data: dict[str, list[EvidenceRecord]]) -> list[EvidenceCluster]:
        """汇总簇数据并构造证据聚类对象。"""
        result: list[EvidenceCluster] = []
        for cluster_id, cluster_records in data.items():
            section_key = cluster_id.removeprefix("cluster_")
            dimension = dimension_for_key(section_key)
            label = dimension.title if dimension else "其他相关讨论"
            result.append(
                EvidenceCluster(
                    id=cluster_id,
                    label=label,
                    summary=f"{label}相关讨论，共 {len(cluster_records)} 条证据。",
                    member_record_ids=[r.id for r in cluster_records],
                    representative_ids=[r.id for r in cluster_records[:5]],
                    size=len(cluster_records),
                )
            )
        return sorted(result, key=lambda cluster: cluster.size, reverse=True)
