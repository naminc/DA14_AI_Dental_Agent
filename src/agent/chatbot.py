import sys
import json
import random
from openai import OpenAI

from src.config import OPENAI_API_KEY, CHAT_MODEL
from src.retriever.search import Retriever
# Đảm bảo bạn đã có file constants.py tương ứng bên Backend (Python)
from src.lib.constants import AI_PERSONAS, AI_TEMPERATURE, AI_SYSTEM_INSTRUCTIONS

class DentalChatbot:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("Thiếu OPENAI_API_KEY trong file .env")

        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.retriever = Retriever()

    def format_history_for_prompt(self, chat_history):
        if not chat_history:
            return "Chưa có lịch sử hội thoại."

        lines = []
        for item in chat_history[-6:]:
            role = "Người dùng" if item["role"] == "user" else "Trợ lý"
            lines.append(f"{role}: {item['content']}")
        return "\n".join(lines)

    def rewrite_query(self, user_question: str, chat_history=None) -> str:
        history_text = self.format_history_for_prompt(chat_history or [])

        prompt = f"""
Hãy viết lại câu hỏi mới nhất thành một câu tìm kiếm rõ ràng hơn cho hệ thống hỏi đáp nha khoa.
Giữ nguyên ý nghĩa, không bịa thêm thông tin. Chỉ trả về đúng 1 câu.

Lịch sử hội thoại:
{history_text}

Câu hỏi mới nhất:
{user_question}
"""

        response = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "Bạn là trợ lý viết lại truy vấn tìm kiếm nha khoa."},
                {"role": "user", "content": prompt}
            ],
            temperature=AI_TEMPERATURE["STRICT"] # Độ chính xác tuyệt đối cho việc tìm kiếm
        )
        return response.choices[0].message.content.strip()

    def build_context(self, results):
        contexts = []
        for item in results:
            block = (
                f"Tiêu đề: {item.get('title', '')}\n"
                f"Mục: {item.get('section', '')}\n"
                f"Nội dung: {item.get('content', '')}\n"
                f"Nguồn: {item.get('source', '')}"
            )
            contexts.append(block)
        return "\n\n---\n\n".join(contexts)

    def answer_stream(self, user_question: str, chat_history=None):
        chat_history = chat_history or []
        selected_persona = random.choice(AI_PERSONAS)
        
        rewritten_question = self.rewrite_query(user_question, chat_history)
        retrieved_docs = self.retriever.search(rewritten_question)
        context = self.build_context(retrieved_docs)
        history_text = self.format_history_for_prompt(chat_history)

        # Ráp nối Prompt từ hằng số
        prompt = f"""
{AI_SYSTEM_INSTRUCTIONS}
Phong cách trả lời hiện tại: {selected_persona}

Lịch sử hội thoại:
{history_text}

Ngữ cảnh nha khoa:
{context}

Câu hỏi người dùng:
{user_question}
"""

        # Bước 2: Gọi API OpenAI với chế độ stream=True
        response = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": f"Bạn là bác sĩ nha khoa chuyên nghiệp, phong cách {selected_persona}. Không nói chuyện phiếm."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=AI_TEMPERATURE["NORMAL"], # Thấp để đảm bảo sự nghiêm túc và nhất quán
            stream=True # KÍCH HOẠT CHẾ ĐỘ STREAM
        )

        # Bước 3: Yield từng mảnh văn bản (text chunks) về cho Backend
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

        # Bước 4: Yield dòng Disclaimer ở cuối cùng (để nó tự động gõ ra sau cùng)
        disclaimer = "\n\n*Thông tin chỉ mang tính tham khảo, không thay thế tư vấn trực tiếp từ bác sĩ nha khoa.*"
        yield disclaimer

        # Bước 5: Yield Metadata (sources, rewritten_query) dưới dạng Dictionary
        # Backend API sẽ bắt Dictionary này để lưu vào Database và trả về cho Frontend làm UI
        yield {
            "sources": retrieved_docs,
            "rewritten_query": rewritten_question
        }