import sys
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

# Thêm đường dẫn gốc vào sys.path để import được module src
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.agent.chatbot import DentalChatbot
from src.database.database import engine, get_db
from src.database import models
from src.auth import router as auth_router
from src.auth.utils import get_current_user

# Khởi tạo Database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dental AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)

try:
    chatbot = DentalChatbot()
except Exception as e:
    print(f"Lỗi khởi tạo Chatbot: {e}")
    chatbot = None

# --- Models ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    user_question: str
    chat_history: List[ChatMessage] = []

# Đã bỏ ChatResponse vì dùng StreamingResponse

# --- Helpers ---
def save_message_to_db(db: Session, session_id: str, user_id: int, role: str, content: str, sources: list = None, rewritten_query: str = None):
    try:
        existing_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
        if not existing_session:
            new_session = models.ChatSession(
                id=session_id,
                user_id=user_id,
                title=content[:50] + "..." if len(content) > 50 else content
            )
            db.add(new_session)
            db.flush()

        new_msg = models.Message(
            session_id=session_id,
            role=role,
            content=content,
            sources=json.dumps(sources, ensure_ascii=False) if sources else None,
            rewritten_query=rewritten_query
        )
        db.add(new_msg)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ LỖI DATABASE: {str(e)}")

# --- Endpoints ---
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if not chatbot: 
        raise HTTPException(status_code=500, detail="Chatbot lỗi")
    
    # 1. Lưu câu hỏi của User vào DB ngay lập tức
    save_message_to_db(db, request.session_id, current_user.id, "user", request.user_question)

    # 2. Tạo Generator để stream câu trả lời của AI
    async def event_generator():
        full_answer = ""
        sources = []
        rewritten_query = ""

        try:
            # Lặp qua các chunk trả về từ hàm answer_stream của chatbot
            for item in chatbot.answer_stream(user_question=request.user_question, chat_history=[m.dict() for m in request.chat_history]):
                if isinstance(item, str):
                    # Nếu là text chunk, cộng dồn và gửi về Frontend
                    full_answer += item
                    yield f"data: {json.dumps({'token': item}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.01) # Tránh nghẽn Event Loop
                elif isinstance(item, dict):
                    # Nếu là dict (metadata ở cuối luồng), lấy ra lưu trữ
                    sources = item.get("sources", [])
                    rewritten_query = item.get("rewritten_query", "")

            # 3. Sau khi AI trả lời xong, tiến hành lưu toàn bộ câu trả lời vào DB
            save_message_to_db(db, request.session_id, current_user.id, "assistant", full_answer, sources, rewritten_query)

            # 4. Gửi tín hiệu kết thúc kèm metadata cho Frontend hiển thị
            yield f"data: {json.dumps({'done': True, 'sources': sources, 'rewritten_query': rewritten_query}, ensure_ascii=False)}\n\n"

        except Exception as e:
            print(f"Stream Error: {e}")
            yield f"data: {json.dumps({'error': 'Lỗi trong quá trình tạo câu trả lời'}, ensure_ascii=False)}\n\n"

    # Trả về StreamingResponse
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/chat/sessions")
def get_sessions(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(models.ChatSession).filter(models.ChatSession.user_id == current_user.id).order_by(models.ChatSession.updated_at.desc()).all()

@app.get("/api/chat/sessions/{session_id}/messages")
def get_messages(session_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id, models.ChatSession.user_id == current_user.id).first()
    if not session: raise HTTPException(status_code=404)
    msgs = db.query(models.Message).filter(models.Message.session_id == session_id).order_by(models.Message.created_at.asc()).all()
    return [{"role": m.role, "content": m.content, "sources": json.loads(m.sources) if m.sources else None} for m in msgs]

# ==========================================
# Endpoints Xóa dữ liệu 
# ==========================================

@app.delete("/api/chat/sessions/{session_id}")
def delete_chat_session(session_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id, 
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc hội thoại để xóa")
    
    try:
        db.query(models.Message).filter(models.Message.session_id == session_id).delete()
        db.delete(session)
        db.commit()
        return {"message": "Đã xóa cuộc hội thoại thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa: {str(e)}")

@app.delete("/api/chat/sessions")
def clear_all_chat_history(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        user_sessions = db.query(models.ChatSession.id).filter(models.ChatSession.user_id == current_user.id).all()
        session_ids = [s[0] for s in user_sessions]
        
        db.query(models.Message).filter(models.Message.session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(models.ChatSession).filter(models.ChatSession.user_id == current_user.id).delete(synchronize_session=False)
        
        db.commit()
        return {"message": "Đã xóa toàn bộ lịch sử thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi dọn dẹp lịch sử: {str(e)}")