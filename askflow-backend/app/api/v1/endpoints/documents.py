from arq import ArqRedis
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.arq_pool import get_arq_pool
from app.db.models import Document, Chunk, Conversation, Message
import shutil
import os
import uuid

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ERROR_MESSAGE_MAX_LEN = 2000


@router.get("")
async def list_documents(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Document.id,
            Document.filename,
            Document.upload_date,
            Document.status,
            Document.error_message,
            func.count(Chunk.id).label("chunk_count"),
        )
        .outerjoin(Chunk, Chunk.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.upload_date.desc())
    )
    result = await db.execute(stmt)
    return [dict(row) for row in result.mappings().all()]


@router.post("/upload", status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    arq_pool: ArqRedis = Depends(get_arq_pool),
):
    # 1. Validate + save file locally
    file_extension = os.path.splitext(file.filename)[1]
    if file_extension.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported for now.")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_extension}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # 2. Create the Document record immediately, marked as processing -
    # actual extraction/chunking/embedding happens in the background (see
    # app/worker.py) so this endpoint returns without waiting on it.
    db_document = Document(
        filename=file.filename,
        file_path=file_path,
        status="processing",
    )
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)

    # 3. Enqueue the background job
    try:
        await arq_pool.enqueue_job("process_document", db_document.id, file_path)
    except Exception as e:
        # The row already exists claiming "processing" but nothing will ever
        # pick it up - fail it explicitly now rather than leaving it stuck
        # forever with no recourse but manual DB surgery.
        db_document.status = "failed"
        db_document.error_message = f"Failed to queue for processing: {e}"[:ERROR_MESSAGE_MAX_LEN]
        await db.commit()
        raise HTTPException(status_code=500, detail="Failed to queue document for processing.")

    return {
        "id": db_document.id,
        "filename": db_document.filename,
        "status": db_document.status,
        "message": "Document uploaded and queued for processing.",
    }


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": document.id,
        "filename": document.filename,
        "upload_date": document.upload_date,
        "status": document.status,
        "error_message": document.error_message,
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # File first, DB second: if disk deletion fails for a real reason
    # (permission/lock), fail loudly and leave the DB row intact so the whole
    # operation stays retryable. A missing file is not an error.
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete file from disk: {e}")

    await db.delete(document)  # cascades to chunks via the model relationship
    await db.commit()

    return {"id": document_id, "message": "Document deleted successfully."}


@router.get("/{document_id}/pdf")
async def get_document_pdf(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Fetch document from DB
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        document.file_path,
        media_type="application/pdf",
        filename=document.filename
    )


@router.get("/{document_id}/conversation")
async def get_conversation(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document.id).where(Document.id == document_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Document not found")

    result = await db.execute(select(Conversation).where(Conversation.document_id == document_id))
    conversation = result.scalar_one_or_none()
    if conversation is None:
        # No conversation yet is a normal state, not an error.
        return {"id": None, "messages": []}

    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.id)
    )
    messages = result.scalars().all()

    return {
        "id": conversation.id,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "citations": m.citations,
                "created_at": m.created_at,
            }
            for m in messages
        ],
    }


@router.delete("/{document_id}/conversation")
async def clear_conversation(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document.id).where(Document.id == document_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Document not found")

    result = await db.execute(select(Conversation).where(Conversation.document_id == document_id))
    conversation = result.scalar_one_or_none()
    if conversation is not None:
        await db.delete(conversation)  # cascades to messages via the model relationship
        await db.commit()

    return {"id": document_id, "message": "Conversation cleared."}
