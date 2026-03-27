# src/chat/dependencies.py
# Dependencies for chat endpoints
# File này để lấy chatbot từ dependencies

from src.agent.chatbot import DentalChatbot

# Chatbot
_chatbot: DentalChatbot | None = None

# Lấy chatbot
def get_chatbot() -> DentalChatbot:
    global _chatbot
    # Nếu chatbot chưa được khởi tạo, khởi tạo chatbot
    if _chatbot is None:
        _chatbot = DentalChatbot()
    # Trả về chatbot
    return _chatbot
