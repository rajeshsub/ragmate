"""Pydantic request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    filename: str
    chunk_count: int
    uploaded_at: str | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class SourceChunk(BaseModel):
    doc_id: str
    chunk_index: int
    score: float
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
