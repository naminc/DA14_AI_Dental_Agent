# BM25 & Tokenization tiếng Việt

Tài liệu giải thích thuật toán BM25 (Sparse Retrieval) và vai trò của Tokenization tiếng Việt bằng Underthesea trong hệ thống DentalAI.

**Tham chiếu mã nguồn:** `src/retriever/search.py` dòng 92-100 (BM25 init), dòng 126-134 (tokenizer)

---

## 1. BM25 là gì?

**BM25 (Best Matching 25)** là thuật toán xếp hạng văn bản dựa trên tần suất từ khóa, thuộc họ TF-IDF. Nó trả lời câu hỏi: "Tài liệu nào chứa nhiều từ khóa của query nhất, có tính đến độ hiếm của từ?"

### Công thức BM25 (Okapi variant)

$$\text{BM25}(Q, D) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

Trong đó:
- $Q = \{q_1, q_2, \ldots, q_n\}$: các token của query
- $f(q_i, D)$: tần suất xuất hiện của token $q_i$ trong tài liệu $D$
- $|D|$: độ dài tài liệu (số token)
- $\text{avgdl}$: độ dài trung bình của tất cả tài liệu
- $k_1 = 1.5$ (mặc định): điều chỉnh mức bão hòa của tần suất
- $b = 0.75$ (mặc định): điều chỉnh ảnh hưởng của độ dài tài liệu

### IDF — Inverse Document Frequency

$$\text{IDF}(q_i) = \ln\left(\frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1\right)$$

- $N$: tổng số tài liệu (762 trong DentalAI)
- $n(q_i)$: số tài liệu chứa token $q_i$

Ý nghĩa: từ xuất hiện trong **ít** tài liệu (hiếm) có IDF cao → được ưu tiên. Từ phổ biến như "và", "là" có IDF thấp → gần như bị loại.

---

## 2. Tại sao cần Tokenization tiếng Việt?

### Vấn đề

Tiếng Việt là ngôn ngữ **đa âm tiết** — một từ có nghĩa có thể gồm 2-3 âm tiết:
- "niềng răng" = 1 khái niệm, nhưng nếu tách theo dấu cách → 2 token "niềng" + "răng"
- "sâu răng" = 1 bệnh, nhưng tách → "sâu" + "răng" (mất nghĩa: "sâu" có thể là con sâu)

Nếu dùng whitespace tokenization (tách theo dấu cách), BM25 sẽ:
- Tìm "răng" trong tất cả tài liệu → quá nhiều kết quả không liên quan
- Không phân biệt "sâu răng" (bệnh) vs "răng sâu" (mô tả)

### Giải pháp: Underthesea Word Tokenizer

Hệ thống sử dụng thư viện **Underthesea** — bộ xử lý ngôn ngữ tự nhiên tiếng Việt:

```python
from underthesea import word_tokenize

word_tokenize("niềng răng có đắt không", format="text")
# → "niềng_răng có đắt không"
```

Kết quả: "niềng_răng" trở thành **1 token duy nhất**, BM25 sẽ khớp chính xác với tài liệu có chứa "niềng_răng".

---

## 3. Pipeline xử lý trong DentalAI

### 3.1. Text Normalization

Trước khi tokenize, văn bản được chuẩn hóa:

```
Input:  "Chi phí Niềng Răng bao nhiêu?"
Step 1: Lowercase         → "chi phí niềng răng bao nhiêu?"
Step 2: Loại bỏ ký tự đặc biệt → "chi phí niềng răng bao nhiêu"
Step 3: Gom khoảng trắng → "chi phí niềng răng bao nhiêu"
```

### 3.2. Vietnamese Tokenization

```
Input:  "chi phí niềng răng bao nhiêu"
Output: ["chi_phí", "niềng_răng", "bao_nhiêu"]
```

Underthesea gộp các cụm từ có nghĩa bằng dấu gạch dưới.

### 3.3. BM25 Corpus Construction

Khi khởi tạo Retriever, corpus BM25 được xây dựng từ metadata đã enriched:

```python
enriched_corpus = [
    f"{title} {section} {summary} {content}"
    for doc in metadata
]
tokenized_corpus = [normalize_and_tokenize(text) for text in enriched_corpus]
bm25 = BM25Okapi(tokenized_corpus)
```

Mỗi tài liệu được biểu diễn bằng danh sách token tiếng Việt. Corpus gồm 762 danh sách token.

---

## 4. Ví dụ minh họa

Query: **"chi phí niềng răng"**

### Bước 1: Tokenize query

```
["chi_phí", "niềng_răng"]
```

### Bước 2: BM25 tính điểm

| Tài liệu | Chứa "chi_phí"? | Chứa "niềng_răng"? | BM25 Score |
|---|---|---|---|
| Doc A — "Niềng răng - Chi phí" | Co | Co | **Cao** |
| Doc B — "Niềng răng - Tổng quan" | Khong | Co | Trung bình |
| Doc C — "Sâu răng - Chi phí" | Co | Khong | Trung bình |
| Doc D — "Chăm sóc răng miệng" | Khong | Khong | 0 |

Doc A chứa **cả hai** token → BM25 score cao nhất.

### Nếu không dùng Underthesea (whitespace tokenization)

```
Query tokens: ["chi", "phí", "niềng", "răng"]
```

- "răng" xuất hiện trong hầu hết 762 tài liệu → IDF rất thấp → gần như vô dụng
- "chi" và "phí" tách rời → có thể khớp với tài liệu không liên quan chứa từ "chi tiết" hoặc "phí tổn"

---

## 5. So sánh BM25 vs Vector Search (FAISS)

| Tiêu chí | BM25 (Sparse) | FAISS (Dense) |
|---|---|---|
| Cách hoạt động | Khớp từ khóa chính xác | Tìm vector ngữ nghĩa gần nhất |
| Thế mạnh | "bảng giá niềng răng" → tìm đúng bài có từ "bảng giá" | "niềng răng có đau không" → hiểu "đau" liên quan đến "cảm giác khó chịu" |
| Điểm yếu | Không hiểu đồng nghĩa: "giá" vs "chi phí" | Có thể trả về bài đúng chủ đề nhưng sai section |
| Tốc độ | Rất nhanh (chỉ đếm token) | Nhanh (Inner Product) nhưng cần load model |

Đây là lý do hệ thống dùng **Hybrid Search** — kết hợp cả hai qua RRF.
