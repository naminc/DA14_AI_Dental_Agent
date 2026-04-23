# Documentation Index — Dental AI Assistant

Thư mục này tập hợp toàn bộ tài liệu kỹ thuật của đồ án Dental AI Assistant. Các tài liệu được viết độc lập, mỗi file bám theo 1 chủ đề, có thể đọc lẻ.

> Mọi tài liệu đều tham chiếu tới file mã nguồn cụ thể (`src/...`, `api/...`) ngay phần mở đầu để dễ đối chiếu.

---

## 1. Lộ trình đọc khuyến nghị

### 1a. Cho người mới

1. [`../README.md`](../README.md) — giới thiệu tổng quan + kiến trúc thư mục.
2. [`INSTALLATION_GUIDE.md`](./INSTALLATION_GUIDE.md) — cài đặt môi trường từ máy trắng.
3. [`RUN_GUIDE.md`](./RUN_GUIDE.md) — thứ tự bật hệ thống + smoke test.
4. [`TECHNICAL_FLOW.md`](./TECHNICAL_FLOW.md) — luồng pipeline end-to-end.

### 1b. Theo chủ đề kỹ thuật

| Quan tâm | Đọc file |
|---|---|
| RAG & Retrieval | `TECHNICAL_FLOW.md`, `RRF_EXPLANATION.md`, `BM25_TOKENIZATION.md`, `MULTI_QUERY_EXPANSION.md` |
| Vector & Toán học | `EMBEDDING_ENGINE.md`, `COSINE_TO_IP_PROOF.md` |
| Chống ảo giác | `HALLUCINATION_GUARDRAILS.md`, `PROMPT_ENGINEERING.md` |
| API & Backend | `API_ARCHITECTURE.md`, `AUTH_SECURITY.md` |
| Frontend | `FRONTEND_ARCHITECTURE.md` |
| Dữ liệu | `DATA_SCHEMA.md` |

---

## 2. Danh sách tài liệu

### 2a. Tài liệu Vận hành

| File | Nội dung | Đối tượng |
|---|---|---|
| [INSTALLATION_GUIDE](./INSTALLATION_GUIDE.md) | Cài Python/Node/MySQL/Ollama, pull model, build FAISS index, troubleshoot | Developer lần đầu setup |
| [RUN_GUIDE](./RUN_GUIDE.md) | Thứ tự bật/tắt, health-check, smoke test, switch engine | Daily dev, demo |

### 2b. Tài liệu Kiến trúc

| File | Nội dung |
|---|---|
| [TECHNICAL_FLOW](./TECHNICAL_FLOW.md) | 5 bước pipeline: Rewrite → Extract + Expand (song song) → Hybrid Search → Context → Stream |
| [API_ARCHITECTURE](./API_ARCHITECTURE.md) | FastAPI entry, Dependency Injection, SSE streaming, Pydantic schemas, lifespan warmup |
| [FRONTEND_ARCHITECTURE](./FRONTEND_ARCHITECTURE.md) | Next.js 16 App Router, Zustand stores, SSE parser, 2FA UX flow |
| [AUTH_SECURITY](./AUTH_SECURITY.md) | JWT + bcrypt + TOTP 2FA, database schema chính xác theo code |
| [DATA_SCHEMA](./DATA_SCHEMA.md) | Dataset v1 (plain text) vs v2 (markdown + summary), pipeline nâng cấp |

### 2c. Tài liệu Thuật toán

| File | Nội dung |
|---|---|
| [EMBEDDING_ENGINE](./EMBEDDING_ENGINE.md) | Strategy Pattern, OpenAIEngine vs LocalEngine (vietnamese-sbert) |
| [BM25_TOKENIZATION](./BM25_TOKENIZATION.md) | Công thức BM25 Okapi + tokenization tiếng Việt qua Underthesea |
| [RRF_EXPLANATION](./RRF_EXPLANATION.md) | Reciprocal Rank Fusion: công thức, hằng số k, trọng số động, ví dụ tính tay |
| [MULTI_QUERY_EXPANSION](./MULTI_QUERY_EXPANSION.md) | LLM sinh biến thể, cross-query score merging |
| [COSINE_TO_IP_PROOF](./COSINE_TO_IP_PROOF.md) | Chứng minh hình thức Cosine ≡ Inner Product + phân tích chi phí SIMD/FMA |

### 2d. Tài liệu AI & Chất lượng

| File | Nội dung |
|---|---|
| [PROMPT_ENGINEERING](./PROMPT_ENGINEERING.md) | 9 quy tắc system prompt, Temperature strategy, Format history khác nhau cho mỗi LLM call |
| [HALLUCINATION_GUARDRAILS](./HALLUCINATION_GUARDRAILS.md) | 4 loại ảo giác, 5 tầng phòng thủ, ma trận ảo giác × tầng |

---

## 3. Bản đồ tài liệu → mã nguồn

Bảng đối chiếu nhanh giữa tài liệu và file code chính:

| Tài liệu | File code chính |
|---|---|
| `TECHNICAL_FLOW` | `src/agent/chatbot.py`, `src/retriever/search.py` |
| `API_ARCHITECTURE` | `api/main.py`, `src/chat/router.py`, `src/chat/dependencies.py` |
| `AUTH_SECURITY` | `src/auth/router.py`, `src/auth/utils.py`, `src/database/models.py` |
| `EMBEDDING_ENGINE` | `src/retriever/engines.py` |
| `BM25_TOKENIZATION` | `src/retriever/search.py` (class `Retriever`) |
| `RRF_EXPLANATION` | `src/retriever/search.py` (`_hybrid_score`) |
| `MULTI_QUERY_EXPANSION` | `src/retriever/search.py` (`expand_queries`, `search`) |
| `COSINE_TO_IP_PROOF` | `src/retriever/engines.py`, `src/retriever/ingest.py` |
| `PROMPT_ENGINEERING` | `src/lib/constants.py` |
| `HALLUCINATION_GUARDRAILS` | `src/lib/constants.py`, `src/agent/chatbot.py`, `src/retriever/search.py` |
| `DATA_SCHEMA` | `tools/upgrade_dataset.py`, `data/raw/*.json` |
| `FRONTEND_ARCHITECTURE` | `frontend/nextjs-app/` (toàn bộ) |

---

## 4. Lưu ý khi cập nhật tài liệu

Nếu đổi code, các chỗ cần đồng bộ:

| Thay đổi code | Tài liệu cần update |
|---|---|
| Thêm biến môi trường mới trong `src/config.py` | `../.env.example` + `../README.md §4.2` + `INSTALLATION_GUIDE.md §4` |
| Thay thuật toán retrieval | `TECHNICAL_FLOW.md`, `RRF_EXPLANATION.md`, `MULTI_QUERY_EXPANSION.md` |
| Sửa system prompt | `PROMPT_ENGINEERING.md`, `HALLUCINATION_GUARDRAILS.md` |
| Thay model LLM/Embedding | `EMBEDDING_ENGINE.md`, `../README.md §7`, `INSTALLATION_GUIDE.md §7` |
| Thay database schema | `AUTH_SECURITY.md §5`, `DATA_SCHEMA.md` nếu liên quan dataset |
| Thay endpoint | `API_ARCHITECTURE.md §6`, `AUTH_SECURITY.md §6` |
| Thay UI flow | `FRONTEND_ARCHITECTURE.md §5` |
