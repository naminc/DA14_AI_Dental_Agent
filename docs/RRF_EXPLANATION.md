# Reciprocal Rank Fusion (RRF) — Tài liệu học tập

Tài liệu giải thích thuật toán RRF được sử dụng trong hệ thống DentalAI để trộn kết quả từ Dense Retrieval (FAISS) và Sparse Retrieval (BM25).

---

## 1. RRF là gì?

Hãy tưởng tượng bạn muốn tìm phòng khám nha khoa tốt nhất. Bạn hỏi **2 người bạn** cho ý kiến:

- **Bạn A** (FAISS — Vector Search): hiểu **ý nghĩa** câu hỏi, tìm tài liệu có nội dung tương đồng về mặt ngữ nghĩa.
- **Bạn B** (BM25 — Keyword Search): tìm tài liệu có chứa đúng **từ khóa** bạn nói.

Mỗi người đưa ra một danh sách xếp hạng riêng. Vấn đề là: **làm sao gộp 2 danh sách thành 1 danh sách duy nhất một cách công bằng?**

**RRF (Reciprocal Rank Fusion)** chính là phương pháp để làm việc đó — nó lấy **thứ hạng** từ mỗi danh sách, chuyển thành điểm số chung, rồi cộng lại.

### Tại sao không cộng thẳng điểm số (raw score)?

Vì điểm số của FAISS và BM25 **hoàn toàn khác bản chất**, không thể so sánh trực tiếp:

| | FAISS (Cosine Similarity) | BM25 |
|---|---|---|
| Thang điểm | 0.0 → 1.0 | 0 → hàng chục, không giới hạn |
| Phân bố | Dồn quanh 0.7–0.9 | Phân tán rộng, phụ thuộc độ dài tài liệu |
| Ý nghĩa | Góc giữa 2 vector | Tần suất từ khóa (TF-IDF variant) |

Cộng 0.85 (FAISS) + 12.7 (BM25) = 13.55 → **BM25 áp đảo hoàn toàn**, FAISS gần như vô nghĩa. Đây là lý do ta cần RRF: **chỉ dùng thứ hạng, bỏ qua điểm số thô**, đưa mọi thứ về cùng một thang đo.

---

## 2. Phân tích công thức RRF

### Công thức gốc (bài báo Cormack 2009)

```
RRF_score(doc) = Σ  1 / (k + rank_i)
```

Trong hệ thống DentalAI, công thức được mở rộng thêm **trọng số động** (weighted RRF):

```
RRF_score(doc) = w_vector / (k + rank_faiss + 1)
               + w_bm25   / (k + rank_bm25  + 1)
```

Tương ứng với code thực tế trong `src/retriever/search.py`:

```python
scores[idx] = (
    w_vector / (self._RRF_K + v_r + 1)
    + w_bm25 / (self._RRF_K + b_r + 1)
)
```

### Ý nghĩa từng thành phần

**`rank`** — thứ hạng của tài liệu trong danh sách (bắt đầu từ 0). Rank = 0 nghĩa là đứng đầu.

**`1 / (k + rank)`** — nghịch đảo thứ hạng. Tài liệu đứng **càng cao** → rank càng nhỏ → điểm **càng lớn**. Tài liệu đứng **thấp hoặc không xuất hiện** → rank rất lớn → điểm **gần 0**.

**`k = 60`** — hằng số làm mượt (smoothing constant). Đây là phần quan trọng nhất, giải thích ở mục tiếp theo.

### Vai trò của hằng số k

Không có k, công thức trở thành `1/rank` — tài liệu rank 1 được **1.0 điểm**, rank 2 chỉ được **0.5 điểm** (giảm 50%). Chênh lệch quá lớn, top 1 áp đảo tất cả.

Khi thêm k = 60:

- Rank 0: `1/(60+0+1) = 0.01639`
- Rank 1: `1/(60+1+1) = 0.01613`
- Rank 2: `1/(60+2+1) = 0.01587`

Chênh lệch giữa các vị trí chỉ còn **rất nhỏ** → tài liệu rank 5 vẫn có cơ hội cạnh tranh với rank 1 nếu nó xuất hiện ở **cả 2 danh sách**.

### k thay đổi thì sao?

| k | Hiệu ứng | Khi nào dùng |
|---|---|---|
| **k = 10** (nhỏ) | Top 1-2 được ưu tiên mạnh, tài liệu rank thấp gần như bị loại | Khi bạn **rất tin** vào thứ hạng ban đầu |
| **k = 60** (mặc định) | Cân bằng — top cao vẫn được ưu tiên nhưng không áp đảo | **Phổ biến nhất**, phù hợp đa số trường hợp |
| **k = 100** (lớn) | Mọi vị trí gần như bằng nhau, RRF chủ yếu đếm "xuất hiện ở bao nhiêu danh sách" | Khi bạn không tin lắm vào ranking riêng lẻ |

---

## 3. Ví dụ minh họa — Tính tay

Giả sử query: **"chi phí niềng răng"** → k = 60, w_vector = 0.3, w_bm25 = 0.7 (câu hỏi keyword-heavy).

### Kết quả từ 2 kênh

| Tài liệu | Rank FAISS | Rank BM25 |
|---|---|---|
| Doc A — "Niềng răng - Tổng quan" | 0 (top 1) | 2 |
| Doc B — "Niềng răng - Chi phí" | 2 | 0 (top 1) |
| Doc C — "Invisalign - Bảng giá" | 1 | không có (miss → rank = 1000) |

### Tính RRF score từng doc

**Doc A:**

```
= 0.3 / (60 + 0 + 1)  +  0.7 / (60 + 2 + 1)
= 0.3 / 61             +  0.7 / 63
= 0.004918             +  0.011111
= 0.016029
```

**Doc B:**

```
= 0.3 / (60 + 2 + 1)  +  0.7 / (60 + 0 + 1)
= 0.3 / 63             +  0.7 / 61
= 0.004762             +  0.011475
= 0.016237  ← CAO NHAT
```

**Doc C:** (không xuất hiện trong BM25 → rank = 1000)

```
= 0.3 / (60 + 1 + 1)  +  0.7 / (60 + 1000 + 1)
= 0.3 / 62             +  0.7 / 1061
= 0.004839             +  0.000660
= 0.005499  ← THAP NHAT
```

### Kết quả xếp hạng cuối cùng

| Hạng | Tài liệu | RRF Score | Phân tích |
|---|---|---|---|
| **1** | Doc B — Chi phí | **0.016237** | BM25 rank 1 + trọng số BM25 cao (0.7) → chiến thắng |
| **2** | Doc A — Tổng quan | 0.016029 | Xuất hiện ở cả 2 danh sách, nhưng BM25 rank thấp hơn |
| **3** | Doc C — Invisalign | 0.005499 | Chỉ có FAISS tìm thấy, BM25 miss → bị phạt nặng |

**Nhận xét:** Doc C dù FAISS rank 1 (rất cao) nhưng vì BM25 không tìm thấy nó (miss rank = 1000) và trọng số BM25 chiếm 0.7, nên nó rớt xuống cuối. Đây chính là cơ chế **chống ám thị chi tiết** — bài quảng cáo thương hiệu cụ thể bị đẩy xuống.

---

## 4. Câu hỏi phản biện và cách trả lời

### Câu hỏi 1: "Tại sao chọn RRF mà không dùng phương pháp khác như CombSUM hay Learned Ranking?"

**Gợi ý trả lời:**

RRF có 3 ưu điểm quyết định cho đồ án này. Thứ nhất, nó **không cần huấn luyện** (unsupervised) — Learned Ranking cần bộ dữ liệu đánh nhãn relevance mà domain nha khoa tiếng Việt chưa có. Thứ hai, RRF **không phụ thuộc vào thang điểm** — CombSUM cộng thẳng raw score nên kênh nào có điểm lớn hơn sẽ áp đảo, cần thêm bước normalization phức tạp. Thứ ba, RRF đã được chứng minh hiệu quả trong bài báo gốc của Cormack (2009) rằng nó đạt kết quả ngang hoặc tốt hơn các phương pháp phức tạp hơn trong hầu hết benchmark.

### Câu hỏi 2: "Hệ thống của em gọi LLM tới 4 lần cho mỗi câu hỏi, có quá tốn kém và chậm không?"

**Gợi ý trả lời:**

Đúng là 4 LLM calls tạo thêm latency, nhưng đây là sự đánh đổi có chủ đích. Call 1 (rewrite) và call 2 (extract category) chỉ dùng max_tokens = 50-100, rất nhanh và rẻ. Call 3 (expand queries) tăng recall đáng kể — nếu bỏ call này, query "chi phí" sẽ không tìm được bài dùng từ "bảng giá". Chỉ call 4 (answer stream) là tốn kém nhất nhưng nó stream nên người dùng thấy phản hồi ngay. Tổng chi phí khoảng 0.001-0.003 USD/câu hỏi với GPT-4.1-mini, chấp nhận được cho hệ thống y khoa đòi hỏi độ chính xác cao.

### Câu hỏi 3: "Trọng số 0.3/0.7 và 0.5/0.5 em chọn dựa trên cơ sở nào? Có thực nghiệm không?"

**Gợi ý trả lời:**

Trọng số được thiết kế dựa trên đặc tính từng loại câu hỏi. Câu hỏi về "chi phí", "quy trình", "bảng giá" mang tính **keyword-specific** — người dùng muốn tìm đúng bài có từ đó, nên BM25 (keyword matching) được tăng lên 0.7. Câu hỏi thông thường như "sâu răng có nguy hiểm không" mang tính **semantic** — cần hiểu ý nghĩa, nên Vector và BM25 cân bằng 0.5/0.5. Hệ thống phát hiện loại câu hỏi tự động qua danh sách tín hiệu từ khóa (signal list) trong code. Nếu có thời gian mở rộng, có thể dùng grid search trên tập test để tìm trọng số tối ưu hơn, nhưng 0.3/0.7 và 0.5/0.5 đã cho kết quả tốt trong thực nghiệm định tính.

---

## Tài liệu tham khảo

- Cormack, G. V., Clarke, C. L. A., & Buettcher, S. (2009). *Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods.* SIGIR 2009.
