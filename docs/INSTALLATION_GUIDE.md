# Hướng dẫn Cài đặt từ A → Z

Tài liệu này hướng dẫn cài đặt hệ thống Dental AI Assistant từ máy trắng, cho cả Windows, macOS và Linux. Mỗi bước đều có phần **kiểm chứng** (verify) để đảm bảo đúng trước khi chuyển bước.

> Ước tính thời gian cài đặt: **~45 phút** nếu mạng ổn định (download model sbert ~420 MB + Ollama model ~1 GB + `node_modules`).

---

## 1. Yêu cầu hệ thống tối thiểu

| Thành phần | Khuyến nghị | Tối thiểu |
|---|---|---|
| RAM | 8 GB | 4 GB (nếu chỉ dùng cloud) |
| VRAM (nếu dùng Ollama) | 4 GB | 2 GB với model Q4 |
| Ổ cứng | 10 GB trống | 5 GB |
| OS | Windows 10+, Ubuntu 22.04+, macOS 12+ | — |
| Kết nối mạng | Có (cho lần cài đầu) | — |

---

## 2. Cài đặt công cụ nền tảng

### 2.1. Python 3.10+

- **Windows:** tải từ <https://python.org/downloads>, **nhớ tick “Add Python to PATH”**.
- **macOS:** `brew install python@3.11`.
- **Ubuntu:** `sudo apt install python3.11 python3.11-venv python3-pip`.

**Kiểm chứng:**
```bash
python --version      # >= 3.10.x
pip --version
```

### 2.2. Node.js 18+ và npm

- Tải LTS từ <https://nodejs.org> (đã bao gồm npm).
- Hoặc dùng `nvm` / `fnm` để quản lý phiên bản.

**Kiểm chứng:**
```bash
node --version        # >= v18
npm --version
```

### 2.3. Git

Tải từ <https://git-scm.com>. Trên Windows nhớ tick “Git Bash Here”.

**Kiểm chứng:** `git --version`.

### 2.4. MySQL 8.0+ hoặc MariaDB 10.6+

Chọn 1 trong 3 cách:

| Cách | Khi nào dùng |
|---|---|
| **Cài MySQL Server chính thức** (<https://dev.mysql.com/downloads/installer/>) | Windows, có root quyền |
| **XAMPP** (<https://www.apachefriends.org>) | Sinh viên quen dùng phpMyAdmin |
| **Docker** (`docker run -p 3306:3306 -e MYSQL_ALLOW_EMPTY_PASSWORD=true mysql:8`) | Không muốn cài native |

**Kiểm chứng:**
```bash
mysql -u root -p -e "SELECT VERSION();"
```

### 2.5. (Tùy chọn) Ollama — nếu muốn chạy LLM local

- Tải: <https://ollama.com/download>.
- **Khuyến nghị GPU NVIDIA** để tốc độ chấp nhận được (≥ 4 GB VRAM).
- CPU-only vẫn chạy được nhưng phản hồi chậm (~15–30 s/câu).

**Kiểm chứng:** `ollama --version`.

---

## 3. Clone mã nguồn & Tạo môi trường Python

```bash
git clone https://github.com/naminc/DA14_AI_Dental_Agent.git
cd DA14_AI_Dental_Agent

# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# Cài thư viện
pip install --upgrade pip
pip install -r requirements.txt
```

> **Lỗi hay gặp trên Windows:** `Activate.ps1` bị chặn bởi Execution Policy. Fix:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

**Kiểm chứng:**
```bash
python -c "import fastapi, faiss, openai, sentence_transformers, underthesea; print('OK')"
```

---

## 4. Tạo & Cấu hình file `.env`

```bash
cp .env.example .env     # macOS/Linux
copy .env.example .env   # Windows
```

### 4.1. Sinh `SECRET_KEY` an toàn

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

→ copy chuỗi 64 ký tự hex vào biến `SECRET_KEY` trong `.env`.

### 4.2. Điền các biến còn lại

Mẫu tối thiểu để chạy **cloud-only** (OpenAI cho cả embedding + LLM):
```env
EMBEDDING_ENGINE=openai
LLM_ENGINE=openai
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXX
OPENAI_CHAT_MODEL=gpt-4.1-mini
TOP_K=10
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/dental_agent_db
SECRET_KEY=<chuỗi sinh ở bước 4.1>
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256
```

Mẫu tối thiểu để chạy **local-only** (miễn phí, không cần OpenAI API key):
```env
EMBEDDING_ENGINE=local
LLM_ENGINE=local
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_CHAT_MODEL=qwen2.5:1.5b-instruct-q4_K_M
TOP_K=10
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/dental_agent_db
SECRET_KEY=<chuỗi sinh ở bước 4.1>
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256
```

Cấu hình **hybrid** (local embedding + cloud LLM) được khuyến nghị: tiết kiệm chi phí embedding, giữ chất lượng reasoning cao.

---

## 5. Tạo Database MySQL

### 5.1. Tạo database trống (tên phải khớp với `DATABASE_URL`)

```sql
CREATE DATABASE dental_agent_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Hoặc qua CLI:
```bash
mysql -u root -p -e "CREATE DATABASE dental_agent_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 5.2. (Tùy chọn) Tạo user riêng cho ứng dụng

```sql
CREATE USER 'dental_app'@'localhost' IDENTIFIED BY 'your-strong-password';
GRANT ALL PRIVILEGES ON dental_agent_db.* TO 'dental_app'@'localhost';
FLUSH PRIVILEGES;
```
Rồi đổi `DATABASE_URL=mysql+pymysql://dental_app:your-strong-password@localhost:3306/dental_agent_db`.

### 5.3. Kiểm chứng kết nối

```bash
python -c "from sqlalchemy import create_engine; import os; from dotenv import load_dotenv; load_dotenv(); create_engine(os.getenv('DATABASE_URL')).connect(); print('DB OK')"
```

> Các bảng `users`, `chat_sessions`, `messages` sẽ được **tự tạo** khi backend start lần đầu (`models.Base.metadata.create_all` trong `api/main.py`). Không cần chạy migration thủ công.

---

## 6. Xây dựng FAISS Index (bắt buộc, chạy 1 lần cho mỗi engine)

### 6.1. Nếu dùng `EMBEDDING_ENGINE=local`

```bash
python -m src.retriever.ingest --engine local
```

Lần đầu sẽ tự tải model `keepitreal/vietnamese-sbert` (~420 MB) về cache HuggingFace (`~/.cache/huggingface/`). Sau đó mã hóa tài liệu, output vào `data/vector_db/local/`:

```
data/vector_db/local/
├── faiss.index      # FAISS IndexFlatIP, 768 dim
└── metadata.json    # docs
```

### 6.2. Nếu dùng `EMBEDDING_ENGINE=openai`

```bash
python -m src.retriever.ingest --engine openai
```

- Cần `OPENAI_API_KEY` hợp lệ.
- Chi phí: ~0.02 USD/1M tokens. Toàn bộ bài ~1M tokens → **~0.02 USD**.
- Output tại `data/vector_db/openai/` (1536 dim).

### 6.3. Có thể build cả hai cùng lúc

Index được lưu tách biệt (`vector_db/local/` vs `vector_db/openai/`). Thay đổi `.env EMBEDDING_ENGINE` là tự động load đúng index, **không cần ingest lại**.

**Kiểm chứng:**
```bash
python -c "import faiss; idx = faiss.read_index('data/vector_db/local/faiss.index'); print(f'Vectors: {idx.ntotal}, Dim: {idx.d}')"
```

---

## 7. (Chỉ khi dùng LLM local) Cài Ollama & Pull model

### 7.1. Pull model đúng theo `.env`

```bash
ollama pull qwen2.5:1.5b-instruct-q4_K_M
```

Kích thước ~1 GB. Có thể chọn model khác bằng cách:
1. Pull model mong muốn: `ollama pull qwen2.5:7b-instruct-q4_K_M` (cần 6 GB VRAM).
2. Sửa `OLLAMA_CHAT_MODEL` trong `.env`.

### 7.2. Bật Ollama với cấu hình tối ưu

**Windows** — chạy `start_ollama.bat` ở root dự án. Script set các biến sau trước khi gọi `ollama serve`:

| Biến | Giá trị | Mục đích |
|---|---|---|
| `OLLAMA_NUM_GPU` | 999 | Đẩy hết layers lên GPU nếu đủ VRAM |
| `OLLAMA_FLASH_ATTENTION` | 1 | Tăng tốc attention computation |
| `OLLAMA_KEEP_ALIVE` | 60m | Giữ model trong RAM/VRAM 60 phút, tránh cold-start |
| `OLLAMA_NUM_PARALLEL` | 3 | Cho phép 3 request chạy song song (vì pipeline có 2 LLM call song song: Extract + Expand) |
| `OLLAMA_MAX_LOADED_MODELS` | 1 | Chỉ load 1 model, tiết kiệm VRAM |

**macOS/Linux** — tương đương:
```bash
OLLAMA_NUM_GPU=999 \
OLLAMA_FLASH_ATTENTION=1 \
OLLAMA_KEEP_ALIVE=60m \
OLLAMA_NUM_PARALLEL=3 \
OLLAMA_MAX_LOADED_MODELS=1 \
ollama serve
```

**Kiểm chứng:**
```bash
curl http://localhost:11434/api/tags
# Hoặc trên Windows PowerShell:
Invoke-RestMethod http://localhost:11434/api/tags
```
→ phải trả về JSON chứa tên model bạn vừa pull.

---

## 8. Smoke-test Backend

```bash
uvicorn api.main:app --reload --port 8000
```

Log mong đợi:
```
[STARTUP] Đang khởi tạo DentalChatbot + load Embedding model...
[STARTUP] DentalChatbot khởi tạo xong trong X.XXs
[STARTUP] Sẵn sàng nhận request.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Truy cập <http://127.0.0.1:8000/docs> — giao diện Swagger UI hiển thị toàn bộ endpoints.

Test endpoint mở (register):
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Test User","email":"test@demo.com","password":"123456","confirm_password":"123456"}'
```

Kỳ vọng HTTP 201 với JSON `{"id":1,"full_name":"...","email":"...","is_2fa_enabled":false}`.

---

## 9. Cài đặt Frontend Next.js

```bash
cd frontend/nextjs-app

# npm (mặc định)
npm install
npm run dev

# hoặc pnpm (nhanh hơn, đã có pnpm-lock.yaml)
pnpm install
pnpm dev
```

Kiểm chứng: mở <http://localhost:3000>, thấy màn hình login/đăng ký của Dental AI.

Biến môi trường frontend (sẵn trong `frontend/nextjs-app/.env.local`):
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api
```
Nếu backend chạy trên máy khác, cập nhật URL này rồi **restart** `npm run dev` (Next.js chỉ đọc `.env.local` khi start).

---

## 10. (Tùy chọn) Trích xuất bài viết mới bằng auto_pipeline

Pipeline hỗ trợ 2 chế độ:

```bash
# Chế độ RAW — đọc bài viết từ file .txt trong folder tools/raw/
python tools/auto_pipeline.py --mode raw --raw-dir raw --output data/test/raw_dental_dataset.json

# Chế độ CRAWL — cào bài viết từ danh sách link
python tools/auto_pipeline.py --mode crawl --links links/test.txt --output data/test/crawl_dental_dataset.json
```

- Cần `OPENAI_API_KEY` trong `.env` (dùng GPT-4.1-mini để bóc tách chunk y khoa).
- Format file `.txt` cho chế độ RAW: mỗi bài cách nhau 1 dòng trống (dòng 1 = URL, dòng 2 = tiêu đề, dòng 3+ = nội dung).
- Auto-save sau mỗi bài, không mất dữ liệu nếu crash giữa chừng.

## 11. (Tùy chọn) Nâng cấp dataset v1 → v2

Nếu muốn tự sinh lại `data/raw/dental_dataset_v2.json`:

```bash
# Cần OPENAI_API_KEY + UPGRADE_DATASET_MODEL trong .env
python tools/upgrade_dataset.py
```

- Script dùng `gpt-4o-mini` (rẻ, ổn định) để sinh `summary` + `content_md`.
- Tự lưu checkpoint mỗi 50 bài → có thể dừng và chạy tiếp (`resume-safe`).
- Chi phí toàn bộ 762 bài: **≈ 0.5–1 USD** tùy độ dài content.

Sau khi có `dental_dataset_v2.json`, chạy lại ingest để FAISS index dùng dữ liệu mới:
```bash
python -m src.retriever.ingest --engine local
```

---

## 12. Các lỗi thường gặp & cách xử lý

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `ValueError: Thieu DATABASE_URL trong file .env` | Thiếu hoặc sai tên biến | Kiểm tra `.env` có `DATABASE_URL=mysql+pymysql://...`, nhớ `load_dotenv()` đã chạy |
| `RuntimeError: SECRET_KEY chưa được cấu hình` | Biến rỗng | Sinh key bằng `secrets.token_hex(32)` → cập nhật `.env` |
| `FileNotFoundError: FAISS index not found` | Chưa chạy ingest | `python -m src.retriever.ingest --engine <local|openai>` |
| `ConnectionError: KHÔNG THỂ KẾT NỐI TỚI OLLAMA` | Ollama chưa bật hoặc sai URL | Chạy `start_ollama.bat`; kiểm tra `OLLAMA_BASE_URL` phải đúng `http://localhost:11434/v1` |
| `ValueError: Thiếu OPENAI_API_KEY trong .env` | `LLM_ENGINE=openai` nhưng chưa có key | Điền key hoặc đổi `LLM_ENGINE=local` |
| Frontend báo `Network Error` / `CORS` | Backend chưa chạy hoặc cổng sai | Đảm bảo backend ở `http://127.0.0.1:8000` + `NEXT_PUBLIC_API_URL` khớp |
| `Access denied for user 'root'@'localhost'` | Sai password MySQL | Sửa `DATABASE_URL` đúng username/password |
| `(2006, "MySQL server has gone away")` | MySQL timeout idle connection | Đã fix: engine cấu hình `pool_pre_ping=True` + `pool_recycle=1800` tự reconnect |
| `ImportError: Could not find the DLL(s) 'libfaiss_avx2.dll'` | Python/FAISS không tương thích | Cài lại `pip install faiss-cpu --no-cache-dir`, dùng Python 3.10/3.11 |
| `from underthesea import word_tokenize` chạy chậm lần đầu | Underthesea lazy-load model | Bình thường — chỉ chậm lần đầu ingest, các lần sau đã cache |

---

## 13. Tổng kết checklist cài đặt

- [ ] Python 3.10+ + `.venv` activated + `pip install -r requirements.txt`
- [ ] Node 18+ + `npm install` trong `frontend/nextjs-app`
- [ ] MySQL đang chạy + database `dental_agent_db` đã được tạo
- [ ] `.env` có đủ: `DATABASE_URL`, `SECRET_KEY`, `TOP_K`, engine keys
- [ ] FAISS index đã build cho engine chọn (`data/vector_db/<engine>/faiss.index` tồn tại)
- [ ] (Nếu local LLM) Ollama đã bật + model đã pull
- [ ] Backend chạy được tại `http://127.0.0.1:8000/docs`
- [ ] Frontend chạy được tại `http://localhost:3000`

Sau khi checklist xanh hoàn toàn, chuyển sang [`RUN_GUIDE.md`](./RUN_GUIDE.md) để biết cách bật/tắt hệ thống gọn gàng mỗi lần làm việc.
