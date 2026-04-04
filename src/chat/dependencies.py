# src/chat/dependencies.py

import time
from src.agent.chatbot import DentalChatbot

_chatbot: DentalChatbot | None = None


def get_chatbot() -> DentalChatbot:
    """Singleton — chỉ khởi tạo DentalChatbot 1 lần duy nhất."""
    global _chatbot
    if _chatbot is None:
        t0 = time.perf_counter()
        _chatbot = DentalChatbot()
        print(f"[STARTUP] DentalChatbot khởi tạo xong trong {time.perf_counter() - t0:.2f}s")
    return _chatbot
