"""InsightAgent 证据聚类节点: 语义聚类优先，不支持则规则聚类。"""

from collections import Counter, defaultdict
from functools import lru_cache
from typing import Any

from engines.common.nodes.base_node import BaseNode
from engines.contracts.config import get_settings
from engines.insight_agent.evidence.models import EvidenceCluster, EvidenceRecord
from engines.insight_agent.state import InsightState

TopicRule = tuple[str, str, tuple[str, ...]]

TOPIC_RULES: list[TopicRule] = [
    (
        "background_overview",
        "事件背景与概览",
        ("通报", "回应", "发布", "声明", "官方", "现场", "视频", "消息", "事件", "起因")
    ),
    (
        "heat_and_spread",
        "舆情热度与传播",
        ("热搜", "传播", "转发", "评论", "点赞", "爆料", "关注", "刷屏", "扩散", "趋势")
    ),
    (
        "sentiment_and_opinion",
        "公众情感与观点",
        ("支持", "反对", "质疑", "吐槽", "愤怒", "担心", "理解", "争议", "态度", "看法")
    ),
    (
        "platform_and_group_diff",
        "平台与群体差异",
        ("微博", "抖音", "小红书", "快手", "网友", "专家", "媒体", "大V", "粉丝", "网民", "自媒体")
    ),
    (
        "deep_causes_and_impact",
        "深层原因与影响",
        ("原因", "影响", "风险", "后续", "舆论", "危机", "信任", "社会", "背后", "监管", "处罚", "问责")
    ),
]

TOPIC_LABELS_BY_ID: dict[str, str] = {
    **{f"cluster_{rule_key}": label for rule_key, label, _ in TOPIC_RULES},
    "cluster_other": "其他讨论",
}


class ClusterNode(BaseNode):
    async def __call__(self, state: InsightState) -> dict[str, Any]:
        evidence_pool = state["evidence_pool"]
        evidence_pool.clusters = self._build_clusters(evidence_pool.records)
        return {"evidence_pool": evidence_pool}

    def _build_clusters(self, records: list[EvidenceRecord]) -> list[EvidenceCluster]:
        if not self._is_semantic_clustering_enabled(records):
            return _cluster_by_rules(records)
        return _cluster_by_semantics(records)

    @staticmethod
    def _is_semantic_clustering_enabled(records: list[EvidenceRecord]) -> bool:
        return (
                get_settings().INSIGHT_CLUSTERING_ENABLED
                and bool(get_settings().INSIGHT_CLUSTER_MODEL)
                and len(records) >= get_settings().INSIGHT_CLUSTER_MIN_CLUSTER_SIZE
        )


def _cluster_by_rules(records: list[EvidenceRecord]) -> list[EvidenceCluster]:
    """
    规则聚类
    :param records:
    :return:
    """
    records_by_cluster: dict[str, list[EvidenceRecord]] = defaultdict(list)

    for record in records:
        cluster_id = _match_rule_cluster_id(record)
        record.cluster_id = cluster_id
        records_by_cluster[cluster_id].append(record)

    return _assemble_clusters(records_by_cluster, infer_labels_from_content=False)


def _match_rule_cluster_id(record: EvidenceRecord) -> str:
    """匹配聚类ID"""
    searchable_text = f"{record.source_keyword} {record.content}"
    for rule_key, _label, keywords in TOPIC_RULES:
        if any(keyword in searchable_text for keyword in keywords):
            return f"cluster_{rule_key}"
    return "cluster_other"


@lru_cache(maxsize=1)
def _load_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(str(get_settings().INSIGHT_CLUSTER_MODEL))


def _cluster_by_semantics(records: list[EvidenceRecord]) -> list[EvidenceCluster]:
    sampled_records = records[: get_settings().INSIGHT_CLUSTER_MAX_RECORDS]
    texts_to_embed = [f"{r.source_keyword} {r.content}".strip() for r in sampled_records]

    embeddings = _load_embedding_model().encode(texts_to_embed, normalize_embeddings=True, show_progress_bar=False)
    cluster_assignments = _assign_kmeans_clusters(embeddings, len(sampled_records))

    records_by_cluster: dict[str, list[EvidenceRecord]] = defaultdict(list)
    for record, cluster_idx in zip(sampled_records, cluster_assignments):
        cluster_id = f"semantic_cluster_{cluster_idx}"
        record.cluster_id = cluster_id
        records_by_cluster[cluster_id].append(record)

    return _assemble_clusters(records_by_cluster, infer_labels_from_content=True)


def _assign_kmeans_clusters(embeddings: Any, record_count: int) -> list[int]:
    """
    聚类计算
    :param embeddings:
    :param record_count:
    :return:
    n_init="auto"：兼顾质量与速度
    random_state=42： 同一批数据运行结果一致
    """
    from sklearn.cluster import KMeans
    optimal_k = _determine_optimal_k(record_count)
    return [int(label) for label in
            KMeans(n_clusters=optimal_k, n_init="auto", random_state=42).fit_predict(embeddings)]


def _determine_optimal_k(record_count: int) -> int:
    """
    计算 K-Means 聚类算法中的最优聚类数量
    :param record_count:
    :return:
    """
    estimated_k = record_count // get_settings().INSIGHT_CLUSTER_MIN_CLUSTER_SIZE
    return max(2, min(get_settings().INSIGHT_CLUSTER_MAX_CLUSTERS, estimated_k, record_count))


def _assemble_clusters(
        records_by_cluster: dict[str, list[EvidenceRecord]],
        *,
        infer_labels_from_content: bool,
) -> list[EvidenceCluster]:
    """
        将分组后的底层证据记录，统一组装为标准化的 EvidenceCluster 簇实体
        标签决断: 根据 `infer_labels_from_content` 决定是基于内容的词频投票动态推断标签，还是降级使用静态规则映射表。
        """
    clusters: list[EvidenceCluster] = []

    for cluster_id, cluster_records in records_by_cluster.items():
        if infer_labels_from_content:
            cluster_label = _infer_cluster_label(cluster_records)
        else:
            cluster_label = TOPIC_LABELS_BY_ID.get(cluster_id, "其他讨论")

        clusters.append(EvidenceCluster(
            id=cluster_id,
            label=cluster_label,
            summary=f"{cluster_label}相关讨论，共 {len(cluster_records)} 条证据。",
            member_record_ids=[r.id for r in cluster_records],
            representative_ids=[r.id for r in cluster_records[:5]],
            size=len(cluster_records),
        ))

    return sorted(clusters, key=lambda c: c.size, reverse=True)


def _infer_cluster_label(cluster_records: list[EvidenceRecord]) -> str:
    sampled_content = " ".join(r.content[:300] for r in cluster_records)
    voted_label = _vote_for_best_label(sampled_content)
    return voted_label if voted_label else "综合讨论簇"


def _vote_for_best_label(sampled_content: str) -> str:
    """是给各个 Label 记票并选出得票最高者"""
    label_hit_counts: Counter[str] = Counter()
    for _rule_key, label, keywords in TOPIC_RULES:
        for keyword in keywords:
            if keyword in sampled_content:
                label_hit_counts[label] += 1
    return label_hit_counts.most_common(1)[0][0] if label_hit_counts else ""


if __name__ == "__main__":
    import asyncio


    async def run_test():
        print("=== 开始初始化 ClusterNode 测试 ===")
        from engines.insight_agent.evidence import EvidencePool, EvidenceRecord, Engagement, RetrievalMeta

        # 1. 构造多条带有鲜明规则特征的测试证据
        test_records = [
            EvidenceRecord(
                id="doc_1", platform="weibo", source_table="weibo_note",
                content="官方刚刚发布声明，通报了本次高考的相关事件调查结果。",
                source_keyword="高考", published_at="2026-07-08 10:00:00", hotness_score=100.0,
                engagement=Engagement(0, 0, 0, 0, 0), retrieval=RetrievalMeta(["高考"], ["keyword_recall"], {})
            ),
            EvidenceRecord(
                id="doc_2", platform="douyin", source_table="douyin_aweme",
                content="今年分数线冲上热搜，全网都在刷屏讨论，传播量极高！",
                source_keyword="高考", published_at="2026-07-08 11:00:00", hotness_score=500.0,
                engagement=Engagement(0, 0, 0, 0, 0), retrieval=RetrievalMeta(["高考"], ["hot_recall"], {})
            ),
            EvidenceRecord(
                id="doc_3", platform="weibo", source_table="weibo_note",
                content="真的太担心自己的成绩了，如果考砸了感觉很崩溃，忍不住吐槽一下...",
                source_keyword="高考", published_at="2026-07-08 12:00:00", hotness_score=50.0,
                engagement=Engagement(0, 0, 0, 0, 0), retrieval=RetrievalMeta(["高考"], ["keyword_recall"], {})
            ),
            EvidenceRecord(
                id="doc_4", platform="douyin", source_table="douyin_aweme",
                content="针对部分考场违规情况，教育局已展开调查，将严厉问责相关责任人。",
                source_keyword="高考", published_at="2026-07-08 13:00:00", hotness_score=200.0,
                engagement=Engagement(0, 0, 0, 0, 0), retrieval=RetrievalMeta(["高考"], ["keyword_recall"], {})
            ),
            EvidenceRecord(
                id="doc_5", platform="weibo", source_table="weibo_note",
                content="中午去吃了个牛肉火锅，毛肚很新鲜，很开心。",
                source_keyword="日常", published_at="2026-07-08 14:00:00", hotness_score=10.0,
                engagement=Engagement(0, 0, 0, 0, 0), retrieval=RetrievalMeta(["日常"], ["keyword_recall"], {})
            ),
        ]

        # 2. 构造状态池
        mock_pool = EvidencePool(query="高考", records=test_records, clusters=[])
        state = {"query": "高考", "evidence_pool": mock_pool}

        # 3. 实例化并执行节点
        node = ClusterNode(None)

        result_state = await node(state)

        # 4. 打印聚类结果
        clusters = result_state["evidence_pool"].clusters
        print(f"\n 聚类执行完毕，共生成 {len(clusters)} 个讨论簇:")
        print("-" * 50)

        for i, cluster in enumerate(clusters, 1):
            print(f"[{i}] 簇 ID: {cluster.id}")
            print(f"     标签: {cluster.label}")
            print(f"     规模: {cluster.size} 条证据")
            print(f"     摘要: {cluster.summary}")
            print(f"     代表 ID: {cluster.representative_ids}")
            print("-" * 50)


    # 启动异步测试
    asyncio.run(run_test())
