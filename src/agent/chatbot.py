from openai import OpenAI

from src.config import (
    OPENAI_API_KEY,
    OPENAI_CHAT_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_MODEL,
    EMBEDDING_ENGINE,
    LLM_ENGINE,
)
from src.retriever.search import Retriever
from src.lib.constants import (
    AI_TEMPERATURE,
    AI_SYSTEM_INSTRUCTIONS,
    AI_USER_PROMPT_TEMPLATE,
    REWRITE_SYSTEM_PROMPT,
    REWRITE_USER_TEMPLATE,
    EXTRACT_CATEGORY_SYSTEM_PROMPT,
    EXTRACT_CATEGORY_USER_TEMPLATE,
)


class DentalChatbot:
    """
    Dental RAG Chatbot với Multi-LLM Engine.
    Hỗ trợ 2 engine cho Text Generation / Query Rewrite:
      - "openai": API OpenAI (gpt-4.1-mini) — cần OPENAI_API_KEY
      - "local":  Ollama localhost (qwen2.5:1.5b) — cần Ollama đang chạy

    """

    # Khởi tạo Chatbot
    def __init__(
        self,
        llm_engine: str = LLM_ENGINE,
        embedding_engine: str = EMBEDDING_ENGINE,
    ) -> None:
        # Khởi tạo LLM Engine
        self.llm_engine: str = llm_engine

        if llm_engine == "openai":
            # Khởi tạo OpenAI Client
            if not OPENAI_API_KEY:
                raise ValueError(
                    "Thiếu OPENAI_API_KEY trong .env (bắt buộc khi LLM_ENGINE=openai)"
                )
            # Khởi tạo OpenAI Client
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            # Khởi tạo Chat Model
            self.chat_model: str = OPENAI_CHAT_MODEL

        elif llm_engine == "local":
            # Khởi tạo Ollama Client
            self.client = OpenAI(
                base_url=OLLAMA_BASE_URL,
                api_key="ollama",
            )
            # Khởi tạo Chat Model
            self.chat_model = OLLAMA_CHAT_MODEL
            self._verify_ollama_connection()

        else:
            raise ValueError(
                f"LLM engine '{llm_engine}' không hợp lệ. Chọn 'openai' hoặc 'local'."
            )

        # Khởi tạo Retriever
        self.retriever = Retriever(engine=embedding_engine)

    # Kiểm tra kết nối Ollama
    def _verify_ollama_connection(self) -> None:
        """Kiểm tra kết nối tới Ollama."""
        try:
            self.client.models.list()
        except Exception:
            raise ConnectionError(
                f"\n{'=' * 60}\n"
                f"  KHÔNG THỂ KẾT NỐI TỚI OLLAMA\n"
                f"  URL: {OLLAMA_BASE_URL}\n"
                f"  Model: {self.chat_model}\n\n"
                f"  Hãy chắc chắn:\n"
                f"    1. Ollama đã được cài đặt (https://ollama.com)\n"
                f"    2. Ollama đang chạy: ollama serve\n"
                f"    3. Model đã được pull: ollama pull {self.chat_model}\n"
                f"{'=' * 60}"
            )

    # Làm sạch lịch sử hội thoại
    def format_history_for_prompt(self, chat_history):
        if not chat_history:
            return "Chưa có lịch sử hội thoại."

        lines = []
        for item in chat_history[-8:]:
            role = "Người dùng" if item["role"] == "user" else "Trợ lý"
            lines.append(f"{role}: {item['content']}")
        return "\n".join(lines)

    # Làm sạch lịch sử hội thoại cho rewrite query
    def format_history_for_rewrite(self, chat_history):
        if not chat_history:
            return "Chưa có lịch sử hội thoại."

        lines = []
        for item in chat_history[-6:]:
            if item["role"] == "user":
                lines.append(f"Người dùng: {item['content']}")
            else:
                first_line = item["content"].split("\n")[0][:120]
                lines.append(f"Trợ lý (tóm tắt): {first_line}...")
        return "\n".join(lines)

    def rewrite_query(self, user_question: str, chat_history=None) -> str:
        history_text = self.format_history_for_rewrite(chat_history or [])
        prompt = REWRITE_USER_TEMPLATE.format(
            history=history_text,
            question=user_question,
        )

        response = self.client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=AI_TEMPERATURE["STRICT"],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()

    # Trích xuất bệnh lý / dịch vụ từ query
    def extract_category(self, query: str) -> list[str] | None:
        # Lấy danh sách bệnh lý / dịch vụ có sẵn
        diseases = self.retriever.get_available_diseases()
        # Nếu không có bệnh lý / dịch vụ nào, trả về None
        if not diseases:
            return None

        # Tạo prompt cho extract_category
        prompt = EXTRACT_CATEGORY_USER_TEMPLATE.format(
            diseases=", ".join(diseases),
            query=query,
        )

        try:
            # Gọi API OpenAI để trích xuất bệnh lý / dịch vụ
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": EXTRACT_CATEGORY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=AI_TEMPERATURE["STRICT"],
                max_tokens=50,
            )

            # Lấy kết quả từ API OpenAI
            result = response.choices[0].message.content.strip()
            # Nếu kết quả là NONE, KHÔNG XÁC ĐỊNH, KHÔNG RÕ, hoặc rỗng, trả về None

            if result.upper() in ("NONE", "KHÔNG XÁC ĐỊNH", "KHÔNG RÕ", ""):
                return None

            # Tách kết quả thành danh sách các từ khóa
            categories = [kw.strip() for kw in result.split("|") if kw.strip()]
            return categories if categories else None

        except Exception:
            # Nếu có lỗi, trả về None
            return None

    # Xây dựng ngữ cảnh
    def build_context(self, results):
        # Nếu không có kết quả, trả về "Không tìm thấy ngữ cảnh liên quan."
        if not results:
            return "Không tìm thấy ngữ cảnh liên quan."
        contexts = []
        # Lặp qua từng kết quả
        for item in results:
            # Tạo phần tóm tắt
            parts = [
                f"Tiêu đề: {item.get('title', '')}",
                f"Mục: {item.get('section', '')}",
            ]
            # Nếu có tóm tắt, thêm vào phần tóm tắt
            if summary := item.get("summary", "").strip():
                parts.append(f"Tóm tắt: {summary}")
            # Thêm nội dung
            parts.append(f"Nội dung: {item.get('content', '')}")
            # Thêm nguồn
            parts.append(f"Nguồn: {item.get('source', '')}")
            # Thêm vào danh sách ngữ cảnh
            contexts.append("\n".join(parts))
        # Kết hợp các phần tóm tắt thành một chuỗi
        return "\n\n---\n\n".join(contexts)

    # Main Answer Pipeline (stream)
    def answer_stream(self, user_question: str, chat_history=None):
        chat_history = chat_history or []
        # Rewrite query
        rewritten_question = self.rewrite_query(user_question, chat_history)
        # Trích xuất bệnh lý / dịch vụ từ query
        categories = self.extract_category(rewritten_question)
        # Tìm kiếm ngữ cảnh
        retrieved_docs = self.retriever.search(
            rewritten_question,
            categories=categories,
        )
        # Xây dựng ngữ cảnh
        context = self.build_context(retrieved_docs)
        # Làm sạch lịch sử hội thoại
        history_text = self.format_history_for_prompt(chat_history)
        # Tạo prompt cho user

        # Gọi API OpenAI để trả lời
        user_prompt = AI_USER_PROMPT_TEMPLATE.format(
            history=history_text,
            context=context,
            question=user_question
        )

        # Gọi API OpenAI để trả lời
        response = self.client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": AI_SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": user_prompt}
            ],
            temperature=AI_TEMPERATURE["NORMAL"],
            stream=True
        )

        # Lặp qua từng chunk
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                # Yield content
                yield content

        disclaimer = "\n\n*Thông tin chỉ mang tính tham khảo, không thay thế tư vấn trực tiếp từ bác sĩ nha khoa.*"
        # Yield disclaimer
        yield disclaimer

        # Yield kết quả
        yield {
            "sources": retrieved_docs,
            "rewritten_query": rewritten_question
        }
