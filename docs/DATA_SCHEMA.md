# Cấu trúc dữ liệu - Dental AI Knowledge Base

Tài liệu mô tả chi tiết cấu trúc dữ liệu của hệ thống, bao gồm quá trình nâng cấp từ v1 sang v2 và lý do thiết kế từng trường.

## Tổng quan dataset

| Thuộc tính | Giá trị |
|---|---|
| Tổng số bài viết | 762 |
| Định dạng file | JSON (mảng các object) |
| Encoding | UTF-8 |
| Nguồn dữ liệu | Vinmec, Pharmacity, và các trang y khoa uy tín |
| File v1 (gốc) | `data/raw/dental_dataset.json` |
| File v2 (nâng cấp) | `data/raw/dental_dataset_v2.json` |

---

## So sánh cấu trúc v1 và v2

### Dataset v1 (dental_dataset.json)

```json
{
  "id": "sau-rang-vinmec-01",
  "title": "Sâu răng",
  "section": "Tổng quan",
  "content": "Sâu răng là tình trạng tổn thương mất mô cứng...",
  "source": "https://www.vinmec.com/vie/benh/sau-rang-4504",
  "source_name": "Vinmec",
  "metadata": {
    "disease": "Sâu răng",
    "source": "Vinmec",
    "topic": "tổng quan"
  }
}
```

### Dataset v2 (dental_dataset_v2.json)

```json
{
  "id": "sau-rang-vinmec-01",
  "title": "Sâu răng",
  "section": "Tổng quan",
  "summary": "Sâu răng là tình trạng tổn thương răng do vi khuẩn, phổ biến ở mọi lứa tuổi và có thể dẫn đến nhiều vấn đề sức khỏe.",
  "content": "# Sâu răng\n\n## Tổng quan\n\n**Sâu răng** là tình trạng tổn thương mất mô cứng...",
  "source": "https://www.vinmec.com/vie/benh/sau-rang-4504",
  "source_name": "Vinmec",
  "metadata": {
    "disease": "Sâu răng",
    "source": "Vinmec",
    "topic": "tổng quan"
  }
}
```

### Bảng so sánh các trường

| Trường | v1 | v2 | Thay đổi |
|---|---|---|---|
| `id` | string | string | Giữ nguyên |
| `title` | string | string | Giữ nguyên |
| `section` | string | string | Giữ nguyên |
| `summary` | _(không có)_ | string | **MỚI** — tóm tắt 1 câu (tối đa 30 từ) |
| `content` | plain text | markdown | **NÂNG CẤP** — chuyển sang Markdown |
| `source` | URL string | URL string | Giữ nguyên |
| `source_name` | string | string | Giữ nguyên |
| `metadata` | object | object | Giữ nguyên |

---

## Mô tả chi tiết từng trường

### `id` (string)

Định danh duy nhất cho mỗi chunk, được **code tự sinh** (không phụ thuộc GPT) theo quy tắc:

```
{tên-bệnh-slug}-{section-slug}-{nguồn-slug}-{số-thứ-tự}

Ví dụ: "sau-rang-khai-niem-nhathuoclongchau-01"
        "viem-nuou-phong-ngua-pharmacity-03"
        "nieng-rang-quy-trinh-vinmec-02"
```

Trong đó `nguồn-slug` được rút gọn từ `source_name` (lấy phần trước dấu `.` đầu tiên, VD: `nhathuoclongchau.com.vn` → `nhathuoclongchau`).

### `title` (string)

Tên bệnh lý hoặc dịch vụ nha khoa chính. Nhiều bài có thể cùng title (VD: 10 bài đều có title "Sâu răng") nhưng khác section.

### `section` (string)

Phân mục nội dung trong cùng một bệnh/dịch vụ. Các giá trị phổ biến:

```
Tổng quan | Nguyên nhân | Triệu chứng | Chẩn đoán |
Điều trị  | Phòng ngừa  | Chi phí      | Khi nào nên đi khám nha
```

Vai trò trong hệ thống RAG:
- Được ghép vào chuỗi embedding: `"Tiêu đề: {title} | Mục: {section} | ..."` → giúp phân biệt ngữ nghĩa giữa "Sâu răng - Nguyên nhân" và "Sâu răng - Điều trị".
- Được dùng trong `_boost_overview()` để nhận diện bài tổng quan.

### `summary` (string) — TRƯỜNG MỚI v2

Câu tóm tắt cực ngắn (tối đa 30 từ tiếng Việt) nắm bắt ý chính của bài viết. Được sinh tự động bởi GPT-4o-mini thông qua script `tools/upgrade_dataset.py`.

```
Ví dụ:
- "Sâu răng là tình trạng tổn thương răng do vi khuẩn, phổ biến ở mọi lứa tuổi."
- "Chi phí niềng răng dao động từ 20-100 triệu tùy phương pháp và cơ sở."
```

**Tại sao cần `summary`:**

| Điểm | Giải thích |
|---|---|
| Tăng chất lượng embedding | Summary đóng vai trò "anchor ngữ nghĩa" — khi content dài và lan man, summary giúp vector tập trung vào ý chính |
| Cải thiện BM25 | Từ khóa quan trọng nhất được nén vào summary, tăng TF-IDF cho thuật ngữ cốt lõi |
| Enriched context | LLM nhận được summary trước content → hiểu bối cảnh nhanh hơn, giảm "lạc đề" khi content quá dài |

### `content` (string) — NÂNG CẤP v2

Nội dung đầy đủ của bài viết, đã được chuyển từ plain text sang Markdown.

**Quy tắc Markdown hóa** (thực hiện bởi GPT-4o-mini):
- Dùng `- ` cho danh sách (không dùng số thứ tự).
- Dùng `**in đậm**` cho thuật ngữ y khoa quan trọng.
- Giữ nguyên 100% nội dung gốc, không thêm bớt.
- Tách đoạn hợp lý bằng dòng trống.

```
v1 (plain text):
"Sâu răng là tình trạng tổn thương mất mô cứng của răng do
quá trình hủy khoáng gây ra bởi vi khuẩn ở mảng bám răng."

v2 (markdown):
"**Sâu răng** là tình trạng tổn thương mất mô cứng của răng do
quá trình hủy khoáng gây ra bởi **vi khuẩn** ở **mảng bám** răng."
```

**Tại sao chuyển sang Markdown:**

| Điểm | Giải thích |
|---|---|
| Cấu trúc hóa nội dung | Heading, list, bold giúp LLM phân tách thông tin tốt hơn khi đọc context |
| Nhấn mạnh thuật ngữ | `**vi khuẩn**` giúp embedding engine nhận diện entity y khoa quan trọng |
| Tương thích frontend | Nội dung có thể render trực tiếp với `react-markdown` nếu cần hiển thị nguồn |

### `source` (string)

URL gốc của bài viết, dùng để trích dẫn nguồn trong câu trả lời.

### `source_name` (string)

Tên ngắn gọn của nguồn (VD: "Vinmec", "VnExpress"). Hiển thị trên UI khi người dùng xem nguồn tham khảo.

### `metadata` (object)

Thông tin phân loại phục vụ pre-filtering:

| Trường con | Kiểu | Mô tả |
|---|---|---|
| `disease` | string | Tên bệnh/dịch vụ chính (dùng cho category pre-filter) |
| `source` | string | Tên nguồn (trùng với `source_name`) |
| `topic` | string | Chủ đề phân mục (trùng với `section` dạng lowercase) |

`metadata.disease` là trường quan trọng nhất — được `extract_category()` sử dụng để thu hẹp không gian tìm kiếm. Danh sách disease bao gồm:

```
Sâu răng, Viêm nha chu, Viêm nướu, Niềng răng, Implant,
Răng sứ, Tẩy trắng răng, Nhổ răng khôn, Răng trẻ em,
Chăm sóc răng miệng, ...
```

---

## Quy trình thu thập & xử lý dữ liệu

### Pipeline trích xuất bài viết (`tools/auto_pipeline.py`)

Hỗ trợ 2 chế độ qua `--mode`:

```bash
# Chế độ 1: RAW — đọc bài viết từ file .txt trong folder tools/raw/
python tools/auto_pipeline.py --mode raw --raw-dir raw --output data/test/raw_dental_dataset.json

# Chế độ 2: CRAWL — cào bài viết từ danh sách link
python tools/auto_pipeline.py --mode crawl --links links/test.txt --output data/test/crawl_dental_dataset.json
```

**Format file .txt** (mỗi bài cách nhau bằng 1 dòng trống):
```
https://url-bai-viet-1
Tiêu đề bài viết 1
Nội dung bài viết...

https://url-bai-viet-2
Tiêu đề bài viết 2
Nội dung bài viết...
```

Cả 2 chế độ đều gửi nội dung tới GPT-4.1-mini để bóc tách thành các chunk y khoa. ID được code tự sinh (không phụ thuộc GPT) theo quy tắc `{bệnh}-{section}-{nguồn}-{số}`.

### Quy trình nâng cấp dữ liệu (v1 → v2)

```
┌──────────────────────┐
│  dental_dataset.json │  762 bài, plain text
│  (v1)                │
└──────────┬───────────┘
           │
           v
┌──────────────────────────────────────────────┐
│  tools/upgrade_dataset.py                    │
│                                              │
│  Với mỗi bài viết:                           │
│    1. Gửi title + section + content          │
│       tới GPT-4o-mini                        │
│    2. Nhận về JSON:                          │
│       {"summary": "...", "content_md": "..."}│
│    3. Ghép vào object gốc                    │
│                                              │
│  Checkpoint: lưu mỗi 50 bài                 │
│  Retry: tối đa 5 lần với exponential backoff│
│  Resume-safe: bỏ qua bài đã xử lý          │
└──────────┬───────────────────────────────────┘
           │
           v
┌──────────────────────┐
│ dental_dataset_v2.json│  762 bài, markdown + summary
│  (v2)                │
└──────────┬───────────┘
           │
           v
┌──────────────────────────────────────────────┐
│  python -m src.retriever.ingest              │
│                                              │
│  1. Đọc v2 (fallback v1 nếu chưa có)        │
│  2. Ghép: title | section | summary | content│
│  3. Encode vectors (L2-normalized)           │
│  4. Lưu FAISS IndexFlatIP + metadata.json   │
└──────────────────────────────────────────────┘
```

---

## Tác động của cấu trúc v2 lên hệ thống RAG

### 1. Embedding chất lượng cao hơn

Chuỗi embedding v1:

```
"Tiêu đề: Sâu răng | Nội dung: Sâu răng là tình trạng..."
```

Chuỗi embedding v2:

```
"Tiêu đề: Sâu răng | Mục: Tổng quan | Tóm tắt: Sâu răng là tình trạng
 tổn thương răng do vi khuẩn, phổ biến ở mọi lứa tuổi | Nội dung: ..."
```

Thêm `section` và `summary` giúp vector mang nhiều tín hiệu ngữ nghĩa hơn, đặc biệt khi content quá dài khiến embedding bị "loãng".

### 2. BM25 chính xác hơn

Corpus BM25 cũng được enriched tương tự:

```
"{title} {section} {summary} {content}"
```

Từ khóa trong summary có TF-IDF cao hơn vì chúng xuất hiện cô đọng — giúp BM25 ưu tiên đúng tài liệu hơn.

### 3. Context rõ ràng hơn cho LLM

LLM nhận context có cấu trúc rõ ràng:

```
Tiêu đề: Sâu răng
Mục: Tổng quan
Tóm tắt: Sâu răng là tình trạng tổn thương răng do vi khuẩn...
Nội dung: (chi tiết đầy đủ)
Nguồn: https://...
```

Summary đóng vai trò "tóm tắt điều hành" (executive summary) — LLM đọc summary trước để nắm ý chính, sau đó đọc content để lấy chi tiết. Giảm thiểu tình trạng LLM bị "lạc" trong nội dung dài.

### 4. Hỗ trợ giải quyết "Ám thị chi tiết"

Khi nhiều tài liệu cùng bệnh được trả về, summary giúp LLM nhận ra sự khác biệt giữa:
- Bài tổng quan (summary: "Niềng răng là phương pháp chỉnh nha phổ biến...")
- Bài thương hiệu cụ thể (summary: "Invisalign sử dụng khay trong suốt...")

Kết hợp với Rule 9 trong system prompt, LLM có đủ thông tin để phân biệt bài chung vs bài riêng, tránh trả lời thiên lệch.
