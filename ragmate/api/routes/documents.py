"""Document upload, list, and delete endpoints."""

from __future__ import annotations

import asyncio
import json
import shutil
import threading
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from ragmate.api.auth import require_api_key
from ragmate.api.dependencies import get_ingestion_pipeline, get_vector_store
from ragmate.api.models import DocumentListResponse, DocumentResponse
from ragmate.config import get_settings
from ragmate.core.ingestion.parsers import SUPPORTED_EXTENSIONS
from ragmate.core.ingestion.pipeline import IngestionPipeline
from ragmate.core.storage.chroma import VectorStore

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", summary="Upload and ingest a document (SSE progress stream)")
async def upload_document(
    file: UploadFile,
    _: str = Depends(require_api_key),
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
) -> StreamingResponse:
    settings = get_settings()

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{suffix}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = settings.upload_dir / f"{uuid.uuid4()}{suffix}"

    try:
        with tmp_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    size_mb = tmp_path.stat().st_size / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        tmp_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_mb} MB limit.",
        )

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    filename = file.filename or "unknown"

    def run_ingest() -> None:
        def on_progress(event: dict[str, Any]) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, event)

        try:
            result = pipeline.ingest(tmp_path, filename, on_progress=on_progress)
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"stage": "done", "pct": 100, "message": "Done!", **result},
            )
        except ValueError as exc:
            loop.call_soon_threadsafe(queue.put_nowait, {"stage": "error", "detail": str(exc)})
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, {"stage": "error", "detail": str(exc)})
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    threading.Thread(target=run_ingest, daemon=True).start()

    async def event_stream() -> AsyncGenerator[str]:
        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event)}\n\n"
            if event["stage"] in ("done", "error"):
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("", response_model=DocumentListResponse, summary="List all documents")
async def list_documents(
    _: str = Depends(require_api_key),
    store: VectorStore = Depends(get_vector_store),
) -> DocumentListResponse:
    docs = store.list_documents()
    items = [
        DocumentResponse(
            id=d["id"],
            filename=d.get("filename", ""),
            chunk_count=int(d.get("chunk_count", 0)),
            uploaded_at=d.get("uploaded_at"),
        )
        for d in docs
    ]
    return DocumentListResponse(documents=items, total=len(items))


@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its vectors",
)
async def delete_document(
    doc_id: str,
    _: str = Depends(require_api_key),
    store: VectorStore = Depends(get_vector_store),
) -> None:
    deleted = store.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
