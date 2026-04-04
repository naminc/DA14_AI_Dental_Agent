# Prompt Engineering — Thiết kế Prompt cho hệ thống RAG Nha khoa

Tài liệu giải thích chiến lược thiết kế prompt trong DentalAI, bao gồm 9 quy tắc cứng của System Instructions, cơ chế Query Rewrite, và Entity Extraction.

**Tham chiếu mã nguồn:** `src/lib/constants.py` (toàn bộ prompt), `src/agent/chatbot.py` (logic gọi LLM)

---

## 1. Tổng quan kiến trúc Prompt

Hệ thống sử dụng 4 LLM call, mỗi call có prompt riêng biệt:

| LLM Call | System Prompt | User Template | Temperature |
|---|---|---|---|
| Rewrite Query | `REWRITE_SYSTEM_PROMPT` | `REWRITE_USER_TEMPLATE` | 0.0 (STRICT) |
| Extract Category | `EXTRACT_CATEGORY_SYSTEM_PROMPT` | `EXTRACT_CATEGORY_USER_TEMPLATE` | 0.0 (STRICT) |
| Expand Queries | `EXPAND_QUERY_SYSTEM_PROMPT` | (query trực tiếp) | 0.5 |
| Answer Stream | `AI_SYSTEM_INSTRUCTIONS` | `AI_USER_PROMPT_TEMPLATE` | 0.3 (NORMAL) |

Tất cả prompt được tập trung trong file `constants.py` — tách biệt hoàn toàn khỏi logic code, dễ review và chỉnh sửa.

---

## 2. System Instructions — 9 Quy tắc cứng

Đây là system prompt cho LLM call cuối cùng (Answer Stream), định nghĩa nhân cách và hành vi:

**Persona:** "Bạn là một bác sĩ nha khoa chuyên nghiệp người Việt Nam"

### Rule 1: Không cảm thán thừa thãi

```
KHÔNG dùng: "Ồ", "À", "Vâng", "Chào bạn", "Dạ"
CÓ dùng: Câu dẫn nhập ngắn gọn đi thẳng trọng tâm
VD: "Để chăm sóc răng sau khi niềng, bạn cần lưu ý các bước sau:"
```

Lý do: Chatbot y khoa cần tông chuyên nghiệp, không giống chatbot giải trí.

### Rule 2: Strict Grounding (CỐT LÕI)

```
CHỈ ĐƯỢC PHÉP trả lời dựa trên "Ngữ cảnh nha khoa liên quan" do hệ thống cung cấp.
```

Đây là quy tắc **chống ảo giác (hallucination)** quan trọng nhất. LLM không được dùng kiến thức tự có — mọi thông tin phải trích từ context do Retriever cung cấp.

### Rule 3: Từ chối khi không có dữ liệu

```
Nếu ngữ cảnh không liên quan → trả đúng 1 câu cố định:
"Hiện tại kho dữ liệu của hệ thống chưa có thông tin cụ thể về vấn đề này.
Bạn nên tham khảo trực tiếp ý kiến của bác sĩ nha khoa để có câu trả lời chính xác nhất."
```

Câu từ chối được **hard-code** để đảm bảo consistency — LLM không được tự sáng tạo câu từ chối.

### Rule 4: Giới hạn chuyên môn

```
CHỈ trả lời câu hỏi nha khoa. Từ chối lịch sự nếu ngoài phạm vi.
```

### Rule 5: Ngôn ngữ chuyên nghiệp

```
Trang trọng, khoa học, dễ hiểu — phù hợp bệnh nhân phổ thông lẫn người có hiểu biết y khoa.
```

### Rule 6: Plain text only

```
KHÔNG dùng Markdown (**, #, [ ]). Trả lời bằng văn bản thuần.
```

Lý do: Frontend tự xử lý render, tránh markdown lồng nhau gây lỗi hiển thị.

### Rule 7: Format liệt kê

```
Dùng "-" để liệt kê. KHÔNG để dòng trống giữa các mục liệt kê liên tiếp.
```

Đảm bảo output format nhất quán, dễ parse phía frontend.

### Rule 8: Không disclaimer

```
KHÔNG tự thêm dòng lưu ý cuối — hệ thống tự thêm disclaimer cố định.
```

Disclaimer được append bởi code (`answer_stream()`), không phải LLM. Tránh trùng lặp.

### Rule 9: Chống ám thị chi tiết (QUAN TRỌNG NHẤT)

```
Nếu câu hỏi chung → BẮT BUỘC tổng hợp câu trả lời khái quát.
KHÔNG lấy thông tin thương hiệu cụ thể để trả lời câu hỏi chung.
Nếu ngữ cảnh chỉ có 1 hãng → phải ghi rõ: "Theo quy trình của [Tên Hãng]..."
```

Giải quyết vấn đề: Khi ngữ cảnh chứa nhiều bài về Invisalign, LLM có xu hướng trình bày quy trình Invisalign như quy trình niềng răng chung. Rule 9 bắt LLM phải nhận diện và ghi rõ nguồn.

---

## 3. Query Rewrite — Contextualization

### Mục đích

Biến câu hỏi follow-up (thiếu ngữ cảnh) thành câu truy vấn tìm kiếm độc lập:

```
Lịch sử: "niềng răng là gì?" → "Niềng răng là phương pháp..."
Câu mới: "có đắt không?"
→ Rewrite: "chi phí niềng răng tổng quan các loại phổ biến"
```

### Các quy tắc Rewrite

1. **Ghép chủ đề từ câu trước** vào câu follow-up
2. **Không thêm chi tiết** (tên răng, vị trí, thương hiệu) nếu người dùng không nhắc
3. **Thêm "tổng quan"** cho câu hỏi mang tính tra cứu chung → ưu tiên bài khái quát

### Chuẩn bị lịch sử

Lịch sử chat được format khác nhau cho Rewrite vs Answer:

| | Rewrite (`format_history_for_rewrite`) | Answer (`format_history_for_prompt`) |
|---|---|---|
| Số message | 6 gần nhất | 8 gần nhất |
| Nội dung assistant | Chỉ dòng đầu, cắt 120 ký tự | Đầy đủ |
| Mục đích | Đủ để hiểu chủ đề, không thừa | Đủ ngữ cảnh để trả lời tự nhiên |

---

## 4. Entity Extraction — Phân loại bệnh lý

### Mục đích

Trích xuất tên bệnh/dịch vụ từ query để **pre-filter** kết quả tìm kiếm:

```
"chi phí niềng răng tổng quan" → ["niềng răng"]
"cách chăm sóc răng miệng"    → None (quá chung, không filter)
```

### Danh mục

LLM nhận danh sách bệnh/dịch vụ có sẵn trong dataset (`get_available_diseases()`) và trích xuất từ query. Nếu không khớp → trả về `NONE` → tìm kiếm trên toàn bộ 762 tài liệu.

### Tác động

| Có category | Không có category |
|---|---|
| 762 → ~60 tài liệu | 762 tài liệu |
| Precision cao, recall giảm nhẹ | Recall tối đa, nhiều noise hơn |

---

## 5. Temperature Strategy

| Giá trị | Tên | Dùng cho | Lý do |
|---|---|---|---|
| **0.0** | STRICT | Rewrite, Extract | Cần chính xác tuyệt đối, không sáng tạo |
| **0.3** | NORMAL | Answer Stream | Đủ tự nhiên, không cứng nhắc, vẫn grounded |
| **0.5** | (inline) | Expand Queries | Cần đa dạng từ đồng nghĩa |
| **0.7** | CREATIVE | Dự phòng | Chưa sử dụng, dự phòng cho tương lai |

Nguyên tắc: Nhiệm vụ càng cần **chính xác** → temperature càng **thấp**. Nhiệm vụ càng cần **đa dạng** → temperature càng **cao**.
