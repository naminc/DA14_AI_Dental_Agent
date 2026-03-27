# Dental AI Assistant - Trợ lý Nha khoa Thông minh

Hệ thống **Retrieval-Augmented Generation (RAG)** chuyên sâu cho lĩnh vực nha khoa, kết hợp kho tri thức từ các bài báo y khoa chính thống với mô hình ngôn ngữ lớn (LLM) để tư vấn sức khỏe răng miệng chính xác, có trích dẫn nguồn.

## Tính năng nổi bật

| Tính năng | Mô tả |
|---|---|
| **Grounded Generation** | Phản hồi chỉ dựa trên bài báo chuyên ngành chính thống (Vinmec, Pharmacity,...), kèm trích dẫn nguồn rõ ràng |
| **Query Contextualization** | Hiểu ngữ cảnh hội thoại, tự động rewrite câu hỏi ngắn ("có đắt không?") thành câu hỏi đầy đủ ("chi phí niềng răng tổng quan") |
| **Hybrid Retrieval** | Kết hợp Vector Search (FAISS) và Keyword Search (BM25) qua Reciprocal Rank Fusion, tối ưu trọng số động theo loại câu hỏi |
| **Multi-Query Expansion** | LLM sinh 2 câu hỏi biến thể từ đồng nghĩa, tăng recall và tránh sót do khác biệt từ khóa |
| **Local & Cloud Hybrid** | Hỗ trợ Ollama (local, miễn phí) cho Embedding và OpenAI (cloud) cho Reasoning, chuyển đổi qua `.env` |
| **Anti-Hallucination** | 9 quy tắc cứng trong system prompt: Strict Grounding, từ chối khi không có dữ liệu, chống ám thị thương hiệu |
| **Xác thực & Bảo mật** | Đăng ký/đăng nhập, JWT token, hỗ trợ xác thực hai yếu tố (2FA/TOTP) |

## Kiến trúc hệ thống

```
DentalAIAssistant/
├── api/
│   └── main.py                  # FastAPI entry point, CORS, routers
├── src/
│   ├── agent/
│   │   └── chatbot.py           # RAG pipeline: rewrite → retrieve → generate
│   ├── retriever/
│   │   ├── engines.py           # Strategy Pattern cho embedding engines
│   │   ├── ingest.py            # Pipeline xây dựng FAISS index
│   │   └── search.py            # Hybrid Search: FAISS + BM25 + RRF
│   ├── chat/
│   │   ├── router.py            # API endpoints cho chat
│   │   ├── schemas.py           # Pydantic models
│   │   └── dependencies.py      # Lazy-init chatbot (DI)
│   ├── auth/
│   │   ├── router.py            # API endpoints cho xác thực
│   │   ├── schemas.py           # Pydantic models
│   │   └── utils.py             # JWT, bcrypt, 2FA
│   ├── database/
│   │   ├── database.py          # SQLAlchemy engine & session
│   │   └── models.py            # User, ChatSession, Message
│   ├── lib/
│   │   └── constants.py         # Tất cả prompt templates & AI config
│   └── config.py                # Cấu hình tập trung (.env)
├── data/
│   ├── raw/
│   │   ├── dental_dataset.json      # Dataset gốc (762 bài)
│   │   └── dental_dataset_v2.json   # Dataset nâng cấp (summary + markdown)
│   ├── processed/
│   │   └── chunks.json              # Bản sao metadata sau ingest
│   └── vector_db/
│       ├── local/                   # FAISS index cho vietnamese-sbert
│       └── openai/                  # FAISS index cho text-embedding-3-small
├── tools/
│   ├── upgrade_dataset.py       # Nâng cấp dataset v1 → v2 (GPT-4o-mini)
│   ├── auto_pipeline.py         # Scrape + trích xuất dữ liệu tự động
│   └── get_links.py             # Thu thập link bài viết nha khoa
├── frontend/
│   └── nextjs-app/              # Next.js 16 + Tailwind + shadcn/ui
└── requirements.txt
```

## Yêu cầu hệ thống

- Python 3.10+
- Node.js 18+ (cho frontend)
- MySQL 8.0+ (hoặc MariaDB)
- (Tùy chọn) Ollama — nếu dùng engine local

## Hướng dẫn cài đặt

### 1. Clone và tạo môi trường

```bash
git clone https://github.com/naminc/DA14_AI_Dental_Agent.git
cd DA14_AI_Dental_Agent

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 2. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 3. Cấu hình môi trường

Sao chép file mẫu và điền thông tin:

```bash
cp .env.example .env
```

Các biến quan trọng:

```env
# Engine lựa chọn
EMBEDDING_ENGINE=local          # hoặc "openai"
LLM_ENGINE=openai               # hoặc "local"

# OpenAI (bắt buộc nếu dùng engine openai)
OPENAI_API_KEY=sk-proj-...
OPENAI_CHAT_MODEL=gpt-4.1-mini

# Ollama (bắt buộc nếu dùng engine local cho LLM)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_CHAT_MODEL=qwen2.5:1.5b

# Database
DATABASE_URL=mysql+pymysql://root@localhost:3306/dental_agent_db

# Auth
SECRET_KEY=<chuỗi-bí-mật-ngẫu-nhiên>
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 4. Xây dựng FAISS index

```bash
# Dùng local embedding (miễn phí, mặc định)
python -m src.retriever.ingest --engine local

# Hoặc dùng OpenAI embedding (trả phí, chất lượng cao hơn)
python -m src.retriever.ingest --engine openai
```

### 5. Khởi chạy Backend

```bash
uvicorn api.main:app --reload --port 8000
```

### 6. Khởi chạy Frontend

```bash
cd frontend/nextjs-app
npm install
npm run dev
```

Truy cập ứng dụng tại `http://localhost:3000`.

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Backend | FastAPI, SQLAlchemy, PyMySQL |
| LLM | OpenAI GPT-4.1-mini / Ollama (qwen2.5) |
| Embedding | text-embedding-3-small / vietnamese-sbert |
| Vector DB | FAISS (IndexFlatIP, Cosine Similarity) |
| Keyword Search | BM25Okapi (rank-bm25) |
| NLP tiếng Việt | Underthesea (word tokenization) |
| Frontend | Next.js 16, React 19, Tailwind CSS, shadcn/ui |
| Auth | JWT, bcrypt, TOTP (pyotp) |
