import logging
import time

from src.agent.chatbot import DentalChatbot

logger = logging.getLogger(__name__)

_chatbot: DentalChatbot | None = None


def get_chatbot() -> DentalChatbot:
    """Singleton — chỉ khởi tạo DentalChatbot duy nhất 1 lần."""
    global _chatbot
    if _chatbot is None:
        t0 = time.perf_counter()
        _chatbot = DentalChatbot()
        logger.info("[STARTUP] DentalChatbot khởi tạo xong trong %.2fs", time.perf_counter() - t0)
    return _chatbot
