from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.ingestion import ingestion_service
from app.services.vector import vector_service
from app.db.models import Document, Chunk
import shutil
import os
import uuid

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Save file locally
        file_extension = os.path.splitext(file.filename)[1]
        if file_extension.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported for now.")
            
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_extension}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Process PDF (Extract Text & Chunks)
        # Note: In production, this should be a background task (Celery/Arq)
        chunks_data = await ingestion_service.process_pdf(file_path)
        
        # 3. Create Document Record
        db_document = Document(
            filename=file.filename,
            file_path=file_path
        )
        db.add(db_document)
        await db.commit()
        await db.refresh(db_document)
        
        # 4. Generate Embeddings & Store Chunks
        for chunk_data in chunks_data:
            embedding = await vector_service.generate_embedding(chunk_data["text"])
            
            db_chunk = Chunk(
                document_id=db_document.id,
                text=chunk_data["text"],
                page_number=chunk_data["page_number"],
                embedding=embedding
            )
            db.add(db_chunk)
            
        await db.commit()
        
        return {
            "id": db_document.id,
            "filename": db_document.filename,
            "chunks_processed": len(chunks_data),
            "message": "Document processed and indexed successfully."
        }
        
    except Exception as e:
        # Cleanup if something fails (optional)
        # if os.path.exists(file_path):
        #    os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
