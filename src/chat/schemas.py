from pydantic import BaseModel


# Chat Message
class ChatMessage(BaseModel):
    role: str
    content: str


# Chat Request
class ChatRequest(BaseModel):
    session_id: str
    user_question: str
    chat_history: list[ChatMessage] = []
