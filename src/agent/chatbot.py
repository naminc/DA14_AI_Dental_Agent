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
from src.lib.constants import AI_TEMPERATURE, AI_SYSTEM_INSTRUCTIONS, AI_USER_PROMPT_TEMPLATE


class DentalChatbot:
    """
    Dental RAG Chatbot với Multi-LLM Engine.
    Hỗ trợ 2 engine cho Text Generation / Query Rewrite:
      - "openai": API OpenAI (gpt-4.1-mini) — cần OPENAI_API_KEY
      - "local":  Ollama localhost (qwen2.5:1.5b) — cần Ollama đang chạy
    Cả hai engine đều tương thích OpenAI SDK, nên toàn bộ logic
    chat.completions.create() giữ nguyên, chỉ khác client + model.
    """

    def __init__(
        self,
        llm_engine: str = LLM_ENGINE,
        embedding_engine: str = EMBEDDING_ENGINE,
    ) -> None:
        self.llm_engine: str = llm_engine

        if llm_engine == "openai":
            if not OPENAI_API_KEY:
                raise ValueError(
                    "Thiếu OPENAI_API_KEY trong .env (bắt buộc khi LLM_ENGINE=openai)"
                )
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.chat_model: str = OPENAI_CHAT_MODEL

        elif llm_engine == "local":
            self.client = OpenAI(
                base_url=OLLAMA_BASE_URL,
                api_key="ollama",
            )
            self.chat_model = OLLAMA_CHAT_MODEL
            self._verify_ollama_connection()

        else:
            raise ValueError(
                f"LLM engine '{llm_engine}' không hợp lệ. Chọn 'openai' hoặc 'local'."
            )

        self.retriever = Retriever(engine=embedding_engine)

    def _verify_ollama_connection(self) -> None:
        """Kiểm tra Ollama có đang chạy không. Raise lỗi rõ ràng nếu không kết nối được."""
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

    # ------------------------------------------------------------------
    # History formatting
    # ------------------------------------------------------------------

    def format_history_for_prompt(self, chat_history):
        if not chat_history:
            return "Chưa có lịch sử hội thoại."

        lines = []
        for item in chat_history[-8:]:
            role = "Người dùng" if item["role"] == "user" else "Trợ lý"
            lines.append(f"{role}: {item['content']}")
        return "\n".join(lines)

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

    # ------------------------------------------------------------------
    # Query Rewriting
    # ------------------------------------------------------------------

    def rewrite_query(self, user_question: str, chat_history=None) -> str:
        history_text = self.format_history_for_rewrite(chat_history or [])

        prompt = f"""Nhiệm vụ: Viết lại câu hỏi mới nhất thành một câu truy vấn tìm kiếm nha khoa độc lập, đầy đủ ngữ cảnh.

Yêu cầu:
- Nếu câu hỏi là follow-up (ví dụ: "có đắt không?", "mất bao lâu?", "điều trị thế nào?"), hãy BẮT BUỘC tìm chủ đề chính (danh từ chỉ bệnh/phương pháp) ở câu liền trước đó để ghép vào.
- Giữ nguyên ý nghĩa gốc, TUYỆT ĐỐI KHÔNG tự ý thêm các chi tiết cụ thể (như tên răng, vị trí, tên phòng khám) nếu người dùng không nhắc đến.
- Chỉ trả về đúng 1 câu truy vấn, không giải thích.

Lịch sử hội thoại:
{history_text}

Câu hỏi mới nhất: {user_question}

Câu truy vấn tìm kiếm:"""

        response = self.client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": "Bạn là trợ lý viết lại truy vấn tìm kiếm cho hệ thống RAG nha khoa. Chỉ trả về câu truy vấn, không giải thích."},
                {"role": "user", "content": prompt}
            ],
            temperature=AI_TEMPERATURE["STRICT"],
            max_tokens=100
        )
        return response.choices[0].message.content.strip()

    # ------------------------------------------------------------------
    # Entity Extraction — trích xuất bệnh lý / dịch vụ từ query
    # ------------------------------------------------------------------

    def extract_category(self, query: str) -> list[str] | None:
        diseases = self.retriever.get_available_diseases()
        if not diseases:
            return None

        diseases_str = ", ".join(diseases)

        prompt = f"""Từ câu hỏi nha khoa bên dưới, hãy trích xuất TÊN BỆNH LÝ hoặc DỊCH VỤ NHA KHOA chính.

Danh mục có sẵn trong hệ thống:
{diseases_str}

Quy tắc:
- Trả về 1-2 từ khóa gốc (tên bệnh/dịch vụ), phân cách bằng dấu |
- Chỉ trả về tên bệnh/dịch vụ, KHÔNG kèm chi phí/triệu chứng/quy trình
- Nếu câu hỏi quá chung hoặc không liên quan đến bệnh/dịch vụ cụ thể nào, trả về NONE

Ví dụ:
- "chi phí niềng răng bao nhiêu" → niềng răng
- "sâu răng có nguy hiểm không" → sâu răng | răng sâu
- "cấy ghép implant mất bao lâu" → implant
- "cách chăm sóc răng miệng hàng ngày" → NONE
- "bọc răng sứ thẩm mỹ giá bao nhiêu" → răng sứ

Câu hỏi: {query}"""

        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là bộ phân loại bệnh lý nha khoa. Chỉ trả về tên danh mục, không giải thích.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=AI_TEMPERATURE["STRICT"],
                max_tokens=50,
            )

            result = response.choices[0].message.content.strip()

            if result.upper() in ("NONE", "KHÔNG XÁC ĐỊNH", "KHÔNG RÕ", ""):
                return None

            categories = [kw.strip() for kw in result.split("|") if kw.strip()]
            return categories if categories else None

        except Exception:
            return None

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    def build_context(self, results):
        if not results:
            return "Không tìm thấy ngữ cảnh liên quan."
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

    # ------------------------------------------------------------------
    # Main answer pipeline (stream)
    # ------------------------------------------------------------------

    def answer_stream(self, user_question: str, chat_history=None):
        chat_history = chat_history or []

        rewritten_question = self.rewrite_query(user_question, chat_history)
        categories = self.extract_category(rewritten_question)

        retrieved_docs = self.retriever.search(
            rewritten_question,
            categories=categories,
        )

        context = self.build_context(retrieved_docs)
        history_text = self.format_history_for_prompt(chat_history)

        user_prompt = AI_USER_PROMPT_TEMPLATE.format(
            history=history_text,
            context=context,
            question=user_question
        )

        response = self.client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": AI_SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": user_prompt}
            ],
            temperature=AI_TEMPERATURE["NORMAL"],
            stream=True
        )

        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

        disclaimer = "\n\n*Thông tin chỉ mang tính tham khảo, không thay thế tư vấn trực tiếp từ bác sĩ nha khoa.*"
        yield disclaimer

        yield {
            "sources": retrieved_docs,
            "rewritten_query": rewritten_question
        }
