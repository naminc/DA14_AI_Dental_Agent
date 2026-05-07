import json
import asyncio
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import iterate_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.agent.chatbot import DentalChatbot
from src.database.database import SessionLocal, get_db
from src.database import models
from src.auth.utils import get_current_user

from src.chat.schemas import ChatRequest
from src.chat.dependencies import get_chatbot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


# Save message

def _save_message(
    db: Session,
    session_id: str,
    user_id: int,
    role: str,
    content: str,
    sources: list | None = None,
    rewritten_query: str | None = None,
) -> None:
    try:
        if not db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first():
            db.add(models.ChatSession(
                id=session_id,
                user_id=user_id,
                title=content[:50] + "..." if len(content) > 50 else content,
            ))
            db.flush()

        db.add(models.Message(
            session_id=session_id,
            role=role,
            content=content,
            sources=json.dumps(sources, ensure_ascii=False) if sources else None,
            rewritten_query=rewritten_query,
        ))
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("LỖI DATABASE khi save message: %s", e)


def _save_message_in_new_session(
    session_id: str,
    user_id: int,
    role: str,
    content: str,
    sources: list | None = None,
    rewritten_query: str | None = None,
) -> None:
    """Mở DB session mới chỉ để lưu 1 message rồi đóng ngay.

    Dùng khi đang stream — không thể giữ session từ Depends(get_db) suốt thời gian
    stream LLM (10–30s) vì sẽ chiếm connection pool và dễ bị MySQL wait_timeout cắt.
    """
    db = SessionLocal()
    try:
        _save_message(db, session_id, user_id, role, content, sources, rewritten_query)
    finally:
        db.close()


# Chat

@router.post("")
async def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user),
    chatbot: DentalChatbot = Depends(get_chatbot),
):
    user_id = current_user.id
    session_id = request.session_id
    user_question = request.user_question
    history = [m.model_dump() for m in request.chat_history]

    logger.info(
        "[CHAT] user_id=%s | session=%s | question=%s",
        user_id, session_id, user_question[:120],
    )

    # Lưu user message vào database
    await asyncio.to_thread(
        _save_message_in_new_session,
        session_id, user_id, "user", user_question,
    )

    async def stream() -> AsyncIterator[bytes]:
        full_answer = ""
        sources: list = []
        rewritten_query = ""

        try:
            sync_gen = chatbot.answer_stream(
                user_question=user_question,
                chat_history=history,
            )

            # iterate_in_threadpool đẩy mỗi bước next() của sync generator sang threadpool
            async for item in iterate_in_threadpool(sync_gen):
                if isinstance(item, str):
                    full_answer += item
                    yield f"data: {json.dumps({'token': item}, ensure_ascii=False)}\n\n".encode("utf-8")
                    await asyncio.sleep(0)
                elif isinstance(item, dict):
                    sources = item.get("sources", [])
                    rewritten_query = item.get("rewritten_query", "")

            await asyncio.to_thread(
                _save_message_in_new_session,
                session_id, user_id, "assistant", full_answer, sources, rewritten_query,
            )

            yield f"data: {json.dumps({'done': True, 'sources': sources, 'rewritten_query': rewritten_query}, ensure_ascii=False)}\n\n".encode("utf-8")

        except asyncio.CancelledError:
            logger.info("Client đã ngắt kết nối stream giữa chừng (session=%s)", session_id)
            raise
        except Exception as e:
            logger.exception("Stream Error: %s", e)
            yield f"data: {json.dumps({'error': 'Lỗi trong quá trình tạo câu trả lời'}, ensure_ascii=False)}\n\n".encode("utf-8")

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# Get sessions
@router.get("/sessions")
def get_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == current_user.id)
        .order_by(models.ChatSession.updated_at.desc())
        .all()
    )


# Get messages
@router.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404)

    msgs = (
        db.query(models.Message)
        .filter(models.Message.session_id == session_id)
        .order_by(models.Message.created_at.asc())
        .all()
    )
    return [
        {
            "role": m.role,
            "content": m.content,
            "sources": json.loads(m.sources) if m.sources else None,
        }
        for m in msgs
    ]


# Delete session
@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc hội thoại để xóa")

    try:
        db.query(models.Message).filter(models.Message.session_id == session_id).delete()
        db.delete(session)
        db.commit()
        return {"message": "Đã xóa cuộc hội thoại thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa: {e}")


# Clear all sessions
@router.delete("/sessions")
def clear_all_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        session_ids = [
            s[0]
            for s in db.query(models.ChatSession.id)
            .filter(models.ChatSession.user_id == current_user.id)
            .all()
        ]

        db.query(models.Message).filter(models.Message.session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(models.ChatSession).filter(models.ChatSession.user_id == current_user.id).delete(synchronize_session=False)

        db.commit()
        return {"message": "Đã xóa toàn bộ lịch sử thành công"}
    except Exception as e:
        db.rollback()
        logger.exception("LỖI DATABASE khi clear all sessions: %s", e)
        raise HTTPException(status_code=500, detail=f"Lỗi khi dọn dẹp lịch sử: {e}")
