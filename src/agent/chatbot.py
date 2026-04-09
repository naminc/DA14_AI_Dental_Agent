import time

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
        is_cloud = self.llm_engine == "openai"
        mode_label = "CLOUD" if is_cloud else "LOCAL"
        t_pipeline = time.perf_counter()
        chat_history = chat_history or []

        print(f"\n[TIME-LOG] Pipeline mode: {mode_label} (LLM_ENGINE={self.llm_engine})")

        t_rewrite = 0.0
        t_extract = 0.0

        if is_cloud:
            # CLOUD: Full pipeline (Rewrite → Extract → Expand → Hybrid → LLM)

            # [1] Rewrite query
            t0 = time.perf_counter()
            rewritten_question = self.rewrite_query(user_question, chat_history)
            t_rewrite = time.perf_counter() - t0
            print(f"[TIME-LOG] Rewrite Query mất: {t_rewrite:.2f}s")

            # [2] Extract category
            t0 = time.perf_counter()
            categories = self.extract_category(rewritten_question)
            t_extract = time.perf_counter() - t0
            print(f"[TIME-LOG] Extract Category mất: {t_extract:.2f}s")

        else:
            # LOCAL: Conditional Rewrite + skip Extract, Expand
            if chat_history:
                t0 = time.perf_counter()
                rewritten_question = self.rewrite_query(user_question, chat_history)
                t_rewrite = time.perf_counter() - t0
                print(f"[TIME-LOG] Rewrite Query mất: {t_rewrite:.2f}s (follow-up)")
            else:
                rewritten_question = user_question
                print(f"[TIME-LOG] Rewrite Query: SKIPPED (first question)")

            categories = None
            print(f"[TIME-LOG] Extract Category: SKIPPED (local mode)")

        # [3] Retrieval (FAISS + BM25 + RRF, expand chỉ khi cloud)
        t0 = time.perf_counter()
        retrieved_docs = self.retriever.search(
            rewritten_question,
            categories=categories,
            expand=is_cloud,
        )
        t_retrieval = time.perf_counter() - t0
        print(f"[TIME-LOG] Retrieval tổng mất: {t_retrieval:.2f}s (chi tiết xem bên trên)")

        context = self.build_context(retrieved_docs)
        history_text = self.format_history_for_prompt(chat_history)

        user_prompt = AI_USER_PROMPT_TEMPLATE.format(
            history=history_text,
            context=context,
            question=user_question
        )

        # [4] LLM Generation (stream)
        t_llm_start = time.perf_counter()
        t_first_token = None

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
                if t_first_token is None:
                    t_first_token = time.perf_counter() - t_llm_start
                    print(f"[TIME-LOG] LLM Time-to-First-Token: {t_first_token:.2f}s")
                yield content

        t_llm_total = time.perf_counter() - t_llm_start
        print(f"[TIME-LOG] LLM Generation tổng: {t_llm_total:.2f}s")

        disclaimer = "\n\n*Thông tin chỉ mang tính tham khảo, không thay thế tư vấn trực tiếp từ bác sĩ nha khoa.*"
        yield disclaimer

        yield {
            "sources": retrieved_docs,
            "rewritten_query": rewritten_question
        }

        t_total = time.perf_counter() - t_pipeline
        print(
            f"\n{'=' * 55}\n"
            f"[TIME-LOG] TỔNG KẾT PIPELINE ({mode_label})\n"
            f"  Rewrite Query     : {t_rewrite:.2f}s{'' if t_rewrite > 0 else ' (skipped)'}\n"
            f"  Extract Category  : {t_extract:.2f}s{'' if t_extract > 0 else ' (skipped)'}\n"
            f"  Retrieval         : {t_retrieval:.2f}s\n"
            f"  LLM First Token   : {t_first_token or 0:.2f}s\n"
            f"  LLM Generation    : {t_llm_total:.2f}s\n"
            f"  TỔNG THỜI GIAN   : {t_total:.2f}s\n"
            f"{'=' * 55}"
        )
