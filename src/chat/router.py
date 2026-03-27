import json
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.agent.chatbot import DentalChatbot
from src.database.database import get_db
from src.database import models
from src.auth.utils import get_current_user

from src.chat.schemas import ChatRequest
from src.chat.dependencies import get_chatbot

router = APIRouter(prefix="/api/chat", tags=["chat"])


# Save message

def _save_message(db: Session, session_id: str, user_id: int, role: str, content: str, sources: list | None = None, rewritten_query: str | None = None) -> None:
    try:
        # Nếu session không tồn tại, tạo session mới
        if not db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first():
            db.add(models.ChatSession(
                id=session_id,
                user_id=user_id,
                title=content[:50] + "..." if len(content) > 50 else content,
            ))
            db.flush()

        # Thêm message vào database
        db.add(models.Message(
            session_id=session_id,
            role=role,
            content=content,
            sources=json.dumps(sources, ensure_ascii=False) if sources else None,
            rewritten_query=rewritten_query,
        ))
        # Commit transaction
        db.commit()
    # Nếu có lỗi, rollback transaction
    except Exception as e:
        db.rollback()
        # In lỗi
        print(f"LỖI DATABASE: {e}")


# Chat

# Chat POST
@router.post("")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    chatbot: DentalChatbot = Depends(get_chatbot),
):
    # Lưu message vào database
    _save_message(db, request.session_id, current_user.id, "user", request.user_question)

    async def stream():
        # Khởi tạo full_answer, sources, rewritten_query
        full_answer = ""
        sources: list = []
        rewritten_query = ""

        try:
            # Lấy câu trả lời từ chatbot
            for item in chatbot.answer_stream(
                user_question=request.user_question,
                chat_history=[m.model_dump() for m in request.chat_history],
            ):
                # Nếu item là string, thêm vào full_answer và yield
                if isinstance(item, str):
                    full_answer += item
                    yield f"data: {json.dumps({'token': item}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.01)
                # Nếu item là dictionary, lấy sources và rewritten_query
                elif isinstance(item, dict):
                    sources = item.get("sources", [])
                    rewritten_query = item.get("rewritten_query", "")

            # Lưu message vào database
            _save_message(db, request.session_id, current_user.id, "assistant", full_answer, sources, rewritten_query)

            # Yield done message
            yield f"data: {json.dumps({'done': True, 'sources': sources, 'rewritten_query': rewritten_query}, ensure_ascii=False)}\n\n"

        except Exception as e:
            # In lỗi
            print(f"Stream Error: {e}")
            yield f"data: {json.dumps({'error': 'Lỗi trong quá trình tạo câu trả lời'}, ensure_ascii=False)}\n\n"

    # Trả về streaming response
    return StreamingResponse(stream(), media_type="text/event-stream")


# Get sessions
@router.get("/sessions")
def get_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Lấy sessions từ database
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
    # Lấy session từ database
    session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404)

    # Lấy messages từ database
    msgs = (
        db.query(models.Message)
        .filter(models.Message.session_id == session_id)
        .order_by(models.Message.created_at.asc())
        .all()
    )
    # Trả về messages
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
    # Lấy session từ database
    session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id)
        .first()
    )
    # Nếu session không tồn tại, trả về lỗi
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc hội thoại để xóa")

    try:
        # Xóa messages từ database
        db.query(models.Message).filter(models.Message.session_id == session_id).delete()
        # Xóa session từ database
        db.delete(session)
        # Commit transaction
        db.commit()
        # Trả về message thành công
        return {"message": "Đã xóa cuộc hội thoại thành công"}
    except Exception as e:
        db.rollback()
        # In lỗi
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa: {e}")


# Clear all sessions
@router.delete("/sessions")
def clear_all_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        # Lấy session ids từ database
        session_ids = [
            s[0]
            for s in db.query(models.ChatSession.id)
            .filter(models.ChatSession.user_id == current_user.id)
            .all()
        ]

        # Xóa messages từ database
        db.query(models.Message).filter(models.Message.session_id.in_(session_ids)).delete(synchronize_session=False)
        # Xóa sessions từ database
        db.query(models.ChatSession).filter(models.ChatSession.user_id == current_user.id).delete(synchronize_session=False)

        # Commit transaction
        db.commit()
        # Trả về message thành công
        return {"message": "Đã xóa toàn bộ lịch sử thành công"}
    except Exception as e:
        db.rollback()
        # In lỗi
        print(f"LỖI DATABASE: {e}")
        # Trả về lỗi
        raise HTTPException(status_code=500, detail=f"Lỗi khi dọn dẹp lịch sử: {e}")
