# Multi-Query Expansion

Tài liệu giải thích kỹ thuật mở rộng truy vấn bằng LLM — sinh nhiều biến thể từ đồng nghĩa để tăng recall trong hệ thống tìm kiếm.

**Tham chiếu mã nguồn:** `src/retriever/search.py` — `expand_queries()` | `src/agent/chatbot.py` — `_safe_expand()` (gọi song song bằng `ThreadPoolExecutor`)

---

## 1. Vấn đề: Vocabulary Mismatch

Khi người dùng hỏi "chi phí niềng răng", nhưng tài liệu trong kho dùng từ "bảng giá chỉnh nha", thì:

- **FAISS** (Vector Search): có thể bắt được vì hiểu ngữ nghĩa "chi phí" ~ "bảng giá"
- **BM25** (Keyword Search): **bỏ sót** vì không có từ "chi phí" trong tài liệu

Đây gọi là **Vocabulary Mismatch** — cùng ý nghĩa nhưng dùng từ ngữ khác nhau.

---

## 2. Giải pháp: LLM sinh biến thể

Trước khi tìm kiếm, hệ thống dùng LLM sinh thêm 2 câu hỏi tương đương nhưng dùng từ ngữ khác:

```
Query gốc:   "chi phí niềng răng tổng quan"
Biến thể 1:  "giá chỉnh nha các loại phổ biến hiện nay"
Biến thể 2:  "bảng giá niềng răng bao nhiêu tiền"
```

Tổng cộng 3 queries được gửi vào Hybrid Search. Kết quả từ cả 3 được cộng điểm RRF → tài liệu xuất hiện ở **nhiều biến thể** được boost tự nhiên.

---

## 3. Luồng xử lý

```
Rewrite Query (tuần tự)
    │
    v
expand_queries() ── chạy SONG SONG với extract_category()
    │                 (ThreadPoolExecutor, max_workers=2)
    v
LLM (EXPAND_QUERY_SYSTEM_PROMPT)
    │
    ├── Biến thể 1 (từ đồng nghĩa)
    ├── Biến thể 2 (từ đồng nghĩa)
    │
    v
[Query gốc, Biến thể 1, Biến thể 2]
    │
    v
Truyền vào Retriever.search(expanded_queries=...)
    │
    v
Mỗi query → _hybrid_score() → {doc_idx: rrf_score}
    │
    v
Cộng điểm across 3 queries
    │
    v
Top-K results
```

> **Lưu ý:** `expand_queries()` được gọi từ `chatbot.py` và kết quả được truyền vào `search()` qua tham số `expanded_queries`. `search()` không tự gọi LLM expand nữa.

### Prompt hệ thống

```
"Bạn là trợ lý mở rộng truy vấn tìm kiếm nha khoa.
Từ câu truy vấn gốc, hãy tạo thêm 2 câu hỏi tương đương
nhưng dùng từ ngữ/từ đồng nghĩa khác.
Giữ nguyên ý nghĩa gốc. Mỗi câu 1 dòng, không đánh số, không giải thích."
```

Temperature = 0.5 — đủ sáng tạo để sinh từ đồng nghĩa nhưng không quá xa ý gốc.

---

## 4. Cross-Query Score Merging

Sau khi mỗi query chạy qua Hybrid Search (FAISS + BM25 + RRF), điểm được cộng lại:

```
Doc A: query_1=0.012 + query_2=0.010 + query_3=0.011 = 0.033
Doc B: query_1=0.008 + query_2=0.000 + query_3=0.009 = 0.017
Doc C: query_1=0.000 + query_2=0.007 + query_3=0.000 = 0.007
```

- Doc A xuất hiện ở cả 3 biến thể → **điểm cao nhất** → rất liên quan
- Doc B xuất hiện ở 2/3 → điểm trung bình
- Doc C chỉ xuất hiện ở 1 biến thể → có thể chỉ khớp từ khóa cục bộ

Cơ chế này gọi là **implicit voting** — tài liệu được "bình chọn" bởi nhiều góc nhìn khác nhau.

---

## 5. Fallback khi LLM lỗi

Nếu LLM không khả dụng (mất kết nối, timeout), `expand_queries()` trả về chỉ query gốc:

```python
except Exception:
    return [query]
```

Hệ thống vẫn hoạt động bình thường với 1 query, chỉ giảm recall. Thiết kế này đảm bảo **graceful degradation** — lỗi phụ không làm sập hệ thống chính.

---

## 6. Tác động đến hiệu năng

| Tiêu chí    | Không có Expansion              | Có Expansion (3 queries)              |
| ----------- | ------------------------------- | ------------------------------------- |
| Recall      | Thấp hơn (bỏ sót từ đồng nghĩa) | Cao hơn đáng kể                       |
| Latency     | 1x Hybrid Search                | 3x Hybrid Search + 1 LLM call         |
| Chi phí LLM | 0                               | ~0.0003 USD/query (max_tokens=200)    |
| Precision   | Cao                             | Tương đương (RRF loại noise tự nhiên) |

Latency tăng khoảng 0.3-0.5s cho LLM call, nhưng Hybrid Search rất nhanh (brute-force 762 docs < 5ms mỗi query) nên tổng latency vẫn chấp nhận được.
