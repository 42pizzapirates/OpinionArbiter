from dataclasses import dataclass
from functools import cached_property
from typing import Iterable

from FlagEmbedding import BGEM3FlagModel


@dataclass(frozen=True)
class VectorEmbedding:
    """BGE-M3 输出的稠密与稀疏混合向量。"""

    dense_vector: list[float]
    sparse_vector: dict[int, float]


class BgeM3Embedder:
    """基于 BGE-M3 的稠密稀疏混合向量化器。"""

    def __init__(self, model_name: str, device: str) -> None:
        self.model_name = model_name
        self.device = device

    @cached_property
    def _model(self):
        """懒加载 BGE-M3 编码模型实例。"""
        kwargs = {"use_fp16": True}
        if self.device:
            kwargs["devices"] = self.device
        return BGEM3FlagModel(self.model_name, **kwargs)

    def encode_documents(self, texts: Iterable[str]) -> list[VectorEmbedding]:
        """批量编码文本为稠密稀疏混合向量。"""
        if isinstance(texts, str):
            texts = [texts]
        items = [text for text in texts]
        if not items:
            return []
        output = self._model.encode(
            items,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )
        dense_vectors = output["dense_vecs"]
        sparse_vectors = output["lexical_weights"]
        return [
            VectorEmbedding(
                dense_vector=list(map(float, dense_vector)),
                sparse_vector=_normalize_sparse_vector(sparse_vector),
            )
            for dense_vector, sparse_vector in zip(dense_vectors, sparse_vectors)
        ]

    def encode_query(self, query: str) -> VectorEmbedding | None:
        """将单条查询文本编码为混合向量。"""
        embeddings = self.encode_documents([query])
        return embeddings[0] if embeddings else None


def _normalize_sparse_vector(sparse_vector: dict) -> dict[int, float]:
    """稀疏向量转整型键并过滤零权重。"""
    return {
        int(token_id): float(weight)
        for token_id, weight in sparse_vector.items()
        if float(weight or 0) > 0
    }
