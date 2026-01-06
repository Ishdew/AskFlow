from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_db
from app.services.vector import vector_service
from app.db.models import Chunk, Document

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    document_id: int

@router.post("/query")
async def chat_query(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Generate Embedding for the query
        query_embedding = await vector_service.generate_embedding(request.message)
        
        # 2. Search for relevant chunks in the database
        # Using pgvector's cosine distance operator (<=>)
        # We need to cast the embedding to string for the SQL query if passing directly, 
        # but SQLAlchemy's vector type helps. 
        # However, for pure asyncpg/SQLAlchemy 2.0 with pgvector, a raw query is often most reliable.
        
        # Format embedding as string for SQL: '[1.0, 2.0, ...]'
        embedding_str = str(query_embedding)
        
        stmt = text("""
            SELECT id, text, page_number, 1 - (embedding <=> :embedding) as similarity
            FROM chunks
            WHERE document_id = :document_id
            ORDER BY embedding <=> :embedding
            LIMIT 5
        """)
        
        result = await db.execute(stmt, {
            "embedding": embedding_str, 
            "document_id": request.document_id
        })
        
        rows = result.fetchall()
        
        if not rows:
             return {
                "answer": "I couldn't find any relevant information in the document to answer your question.",
                "citations": []
            }

        # 3. Construct Context
        context_text = ""
        citations = []
        
        for row in rows:
            # row is (id, text, page_number, similarity)
            # Threshold check (optional)
            if row[3] < 0.5: 
                continue
                
            context_text += f"-- Page {row[2]} --\n{row[1]}\n\n"
            citations.append({
                "page": row[2],
                "text": row[1][:100] + "...", # Preview
                "id": row[0],
                "score": float(row[3])
            })
            
        if not context_text:
             return {
                "answer": "I found some matches but they weren't relevant enough.",
                "citations": []
            }

        # 4. Generate Answer with LLM
        system_prompt = f"""You are a helpful AI assistant designed to answer questions about a user's document.
Use the following context to answer the user's question.
If the answer is not in the context, say you don't know.
Cite the page number if possible.

Context:
{context_text}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message}
        ]
        
        answer = await vector_service.generate_answer(messages)
        
        return {
            "answer": answer,
            "citations": citations
        }

    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
