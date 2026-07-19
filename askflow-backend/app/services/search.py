from typing import Any, Dict, List, Literal, Optional

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

# Reciprocal Rank Fusion constant (standard value from Cormack et al.)
RRF_K = 60

# Each branch of the hybrid search pulls this many candidates before fusion,
# so a chunk that ranks well on one signal but is outside the other signal's
# top-N can still be found by the join. Scaled by the number of selected
# documents so each one still gets a fair-sized slice of the candidate pool
# before the final top-N cut (capped to keep the query cheap).
BASE_BRANCH_LIMIT = 20
MAX_BRANCH_LIMIT = 100


def _branch_limit(document_ids: List[int]) -> int:
    return min(BASE_BRANCH_LIMIT * len(document_ids), MAX_BRANCH_LIMIT)


class SearchService:
    """
    Vector / keyword / hybrid (RRF) search over one or more documents' chunks.
    Ranking is "best N overall" across all selected documents, not a
    guaranteed-per-document split.
    """

    async def search(
        self,
        db: AsyncSession,
        document_ids: List[int],
        query_text: str,
        query_embedding: Optional[List[float]],
        mode: Literal["vector", "keyword", "hybrid"],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        if mode == "vector":
            return await self._vector_search(db, document_ids, query_embedding, limit)
        if mode == "keyword":
            return await self._keyword_search(db, document_ids, query_text, limit)
        return await self._hybrid_search(db, document_ids, query_text, query_embedding, limit)

    async def _vector_search(
        self, db: AsyncSession, document_ids: List[int], query_embedding: List[float], limit: int
    ) -> List[Dict[str, Any]]:
        stmt = text("""
            SELECT id, text, page_number, bounding_box, document_id,
                   1 - (embedding <=> :embedding) AS score
            FROM chunks
            WHERE document_id IN :document_ids
              AND embedding IS NOT NULL
            ORDER BY embedding <=> :embedding
            LIMIT :limit
        """).bindparams(bindparam("document_ids", expanding=True))
        result = await db.execute(stmt, {
            "embedding": str(query_embedding),
            "document_ids": document_ids,
            "limit": limit,
        })
        return [dict(row) for row in result.mappings().all()]

    async def _keyword_search(
        self, db: AsyncSession, document_ids: List[int], query_text: str, limit: int
    ) -> List[Dict[str, Any]]:
        stmt = text("""
            SELECT id, text, page_number, bounding_box, document_id,
                   ts_rank_cd(text_search, websearch_to_tsquery('english', :query_text)) AS score
            FROM chunks
            WHERE document_id IN :document_ids
              AND text_search @@ websearch_to_tsquery('english', :query_text)
            ORDER BY score DESC
            LIMIT :limit
        """).bindparams(bindparam("document_ids", expanding=True))
        result = await db.execute(stmt, {
            "query_text": query_text,
            "document_ids": document_ids,
            "limit": limit,
        })
        return [dict(row) for row in result.mappings().all()]

    async def _hybrid_search(
        self,
        db: AsyncSession,
        document_ids: List[int],
        query_text: str,
        query_embedding: List[float],
        limit: int,
    ) -> List[Dict[str, Any]]:
        stmt = text("""
            WITH vector_search AS (
                SELECT id, text, page_number, bounding_box, document_id,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> :embedding) AS rank
                FROM chunks
                WHERE document_id IN :document_ids
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> :embedding
                LIMIT :branch_limit
            ),
            keyword_search AS (
                SELECT id, text, page_number, bounding_box, document_id,
                       ROW_NUMBER() OVER (
                           ORDER BY ts_rank_cd(text_search, websearch_to_tsquery('english', :query_text)) DESC
                       ) AS rank
                FROM chunks
                WHERE document_id IN :document_ids
                  AND text_search @@ websearch_to_tsquery('english', :query_text)
                ORDER BY ts_rank_cd(text_search, websearch_to_tsquery('english', :query_text)) DESC
                LIMIT :branch_limit
            )
            SELECT
                COALESCE(v.id, k.id) AS id,
                COALESCE(v.text, k.text) AS text,
                COALESCE(v.page_number, k.page_number) AS page_number,
                COALESCE(v.bounding_box, k.bounding_box) AS bounding_box,
                COALESCE(v.document_id, k.document_id) AS document_id,
                (COALESCE(1.0 / (:rrf_k + v.rank), 0.0) + COALESCE(1.0 / (:rrf_k + k.rank), 0.0))::float8 AS score
            FROM vector_search v
            FULL OUTER JOIN keyword_search k ON v.id = k.id
            ORDER BY score DESC
            LIMIT :limit
        """).bindparams(bindparam("document_ids", expanding=True))
        result = await db.execute(stmt, {
            "embedding": str(query_embedding),
            "query_text": query_text,
            "document_ids": document_ids,
            "branch_limit": _branch_limit(document_ids),
            "rrf_k": RRF_K,
            "limit": limit,
        })
        return [dict(row) for row in result.mappings().all()]


search_service = SearchService()
