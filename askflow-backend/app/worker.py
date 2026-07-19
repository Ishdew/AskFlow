import logging

from sqlalchemy import update
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.db.models import Document, Chunk
from app.services.ingestion import ingestion_service
from app.services.vector import vector_service

logger = logging.getLogger("arq.worker")

ERROR_MESSAGE_MAX_LEN = 2000


async def process_document(ctx, document_id: int, file_path: str) -> dict:
    """
    Arq job: extract/chunk/embed a previously-saved PDF and persist its
    chunks. The Document row already exists with status="processing"
    (created by the upload endpoint before this job was enqueued).
    """
    try:
        chunks_data = await ingestion_service.process_pdf(file_path)

        async with AsyncSessionLocal() as session:
            async with session.begin():
                for chunk_data in chunks_data:
                    embedding = await vector_service.generate_embedding(chunk_data["text"])
                    session.add(Chunk(
                        document_id=document_id,
                        text=chunk_data["text"],
                        page_number=chunk_data["page_number"],
                        bounding_box=chunk_data.get("bounding_box"),
                        embedding=embedding,
                    ))
                await session.execute(
                    update(Document).where(Document.id == document_id).values(status="ready")
                )
                # session.begin() commits on clean exit, rolls back on exception -
                # matches the original synchronous endpoint's all-or-nothing shape,
                # so "ready" can never be observed with a partial chunk set.

        return {"document_id": document_id, "chunks_processed": len(chunks_data)}

    except Exception as exc:
        logger.exception("Processing failed for document_id=%s", document_id)
        error_message = str(exc)[:ERROR_MESSAGE_MAX_LEN]
        async with AsyncSessionLocal() as session:
            async with session.begin():
                await session.execute(
                    update(Document)
                    .where(Document.id == document_id)
                    .values(status="failed", error_message=error_message)
                )
        raise


async def on_shutdown(ctx):
    # Close this process's own asyncpg pool cleanly on graceful worker shutdown.
    await engine.dispose()


class WorkerSettings:
    functions = [process_document]
    on_shutdown = on_shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_tries = 1        # arq only auto-retries on explicit Retry/CancelledError
                          # anyway - set explicitly so "no retry" is visible in
                          # code rather than an implicit default a reader would
                          # have to go check.
    job_timeout = 1800    # default is 300s; a large PDF's embedding calls could
                          # exceed that.
