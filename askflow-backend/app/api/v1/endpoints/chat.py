from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.db.models import Conversation, Message
from app.services.vector import vector_service
from app.services.search import search_service

router = APIRouter()

# Only meaningful for cosine-similarity scores (0-1 range). Keyword and hybrid
# scores live on different scales (ts_rank_cd, RRF) - "no rows returned" is the
# only relevance gate for those modes.
VECTOR_SIMILARITY_THRESHOLD = 0.2

# How many prior turns (user+assistant pairs) get fed back into the LLM prompt
# so it can handle natural follow-ups. Retrieval/search itself is unaffected.
MAX_HISTORY_TURNS = 6


class ChatRequest(BaseModel):
    message: str
    document_ids: List[int] = Field(min_length=1)
    primary_document_id: int
    search_mode: Literal["vector", "keyword", "hybrid"] = "hybrid"


async def _get_or_create_conversation(db: AsyncSession, document_id: int) -> Conversation:
    result = await db.execute(select(Conversation).where(Conversation.document_id == document_id))
    conversation = result.scalar_one_or_none()
    if conversation is not None:
        return conversation

    # A double-submit (double-click send, two tabs on the same document) can
    # race here - the unique constraint on document_id is the real guard;
    # this just recovers cleanly instead of raising on the loser.
    conversation = Conversation(document_id=document_id)
    db.add(conversation)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        result = await db.execute(select(Conversation).where(Conversation.document_id == document_id))
        conversation = result.scalar_one()
    return conversation


async def _load_history(db: AsyncSession, document_id: int) -> List[dict]:
    conv_id = (await db.execute(
        select(Conversation.id).where(Conversation.document_id == document_id)
    )).scalar_one_or_none()
    if conv_id is None:
        return []

    rows = (await db.execute(
        select(Message.role, Message.content)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.id.desc())
        .limit(MAX_HISTORY_TURNS * 2)
    )).all()[::-1]
    return [{"role": row.role, "content": row.content} for row in rows]


async def _persist_turn(
    db: AsyncSession,
    document_id: int,
    user_content: str,
    document_ids: List[int],
    search_mode: str,
    answer: str,
    citations: list,
) -> None:
    conversation = await _get_or_create_conversation(db, document_id)
    db.add(Message(
        conversation_id=conversation.id, role="user", content=user_content,
        document_ids=document_ids, search_mode=search_mode,
    ))
    db.add(Message(conversation_id=conversation.id, role="assistant", content=answer, citations=citations))
    await db.commit()


@router.post("/query")
async def chat_query(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    if request.primary_document_id not in request.document_ids:
        raise HTTPException(status_code=400, detail="primary_document_id must be included in document_ids")

    try:
        # 1. Only generate a query embedding when the chosen mode needs one
        # (skips an OpenAI call for pure keyword search)
        query_embedding = None
        if request.search_mode in ("vector", "hybrid"):
            query_embedding = await vector_service.generate_embedding(request.message)

        # 2. Search for relevant chunks using the selected mode, across all
        # selected documents (ranked best-N overall, not split per document)
        rows = await search_service.search(
            db=db,
            document_ids=request.document_ids,
            query_text=request.message,
            query_embedding=query_embedding,
            mode=request.search_mode,
        )

        if not rows:
            answer = "I couldn't find any relevant information in the document(s) to answer your question."
            await _persist_turn(db, request.primary_document_id, request.message,
                                 request.document_ids, request.search_mode, answer, [])
            return {"answer": answer, "citations": []}

        # 3. Construct Context
        multi_document = len(request.document_ids) > 1
        context_text = ""
        citations = []

        for row in rows:
            print(f"DEBUG: Chunk {row['id']} ({request.search_mode}) score: {row['score']}")

            # Threshold check only applies to vector mode - keyword/hybrid scores
            # aren't on a comparable absolute scale.
            if request.search_mode == "vector" and row["score"] < VECTOR_SIMILARITY_THRESHOLD:
                continue

            # Label chunks by document when more than one is in scope, so the
            # model can actually distinguish sources when synthesizing an answer.
            label = f"Document {row['document_id']}, Page {row['page_number']}" if multi_document else f"Page {row['page_number']}"
            context_text += f"-- {label} --\n{row['text']}\n\n"
            citations.append({
                "id": row["id"],
                "document_id": row["document_id"],
                "page": row["page_number"],
                "text": row["text"][:100] + "...",  # Preview
                "score": float(row["score"]) if row["score"] is not None else None,
                "bounding_box": row["bounding_box"],
            })

        if not context_text:
            answer = "I found some matches but they weren't relevant enough."
            await _persist_turn(db, request.primary_document_id, request.message,
                                 request.document_ids, request.search_mode, answer, [])
            return {"answer": answer, "citations": []}

        # 4. Generate Answer with LLM
        citation_instruction = (
            "Cite the document and page number if possible."
            if multi_document
            else "Cite the page number if possible."
        )
        system_prompt = f"""You are a helpful AI assistant designed to answer questions about the user's document(s).
Use the following context to answer the user's question.
If the answer is not in the context, say you don't know.
{citation_instruction}

Context:
{context_text}
"""

        history = await _load_history(db, request.primary_document_id)
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": request.message}
        ]

        answer = await vector_service.generate_answer(messages)

        await _persist_turn(db, request.primary_document_id, request.message,
                             request.document_ids, request.search_mode, answer, citations)

        return {
            "answer": answer,
            "citations": citations
        }

    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
