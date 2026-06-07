"""Query endpoint: ask a question, get answer + sources."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ragmate.api.auth import require_api_key
from ragmate.api.dependencies import get_retrieval_pipeline
from ragmate.api.models import QueryRequest, QueryResponse, SourceChunk
from ragmate.core.retrieval.pipeline import RetrievalPipeline

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse, summary="Ask a question about your documents")
async def query_documents(
    request: QueryRequest,
    _: str = Depends(require_api_key),
    pipeline: RetrievalPipeline = Depends(get_retrieval_pipeline),
) -> QueryResponse:
    try:
        result = pipeline.query(request.question)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    return QueryResponse(
        answer=result["answer"],
        sources=[SourceChunk(**s) for s in result["sources"]],
    )
