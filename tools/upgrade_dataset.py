"""
upgrade_dataset.py

Nâng cấp dental_dataset.json → dental_dataset_v2.json
  - Chuyển content sang Markdown (dùng - cho danh sách)
  - Tạo 1 câu summary cực ngắn cho mỗi bài
  - Tự động lưu tạm sau mỗi 50 bài để tránh mất dữ liệu

Sử dụng: python upgrade_dataset.py
"""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from tqdm import tqdm

load_dotenv()

# Cấu hình
# Input path
INPUT_PATH = Path("data/main/crawl_dental_dataset.json")
OUTPUT_PATH = Path("data/main/crawl_dental_dataset_v2.json")
# Checkpoint interval
CHECKPOINT_INTERVAL = 50

# OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY chưa được set trong .env")
    sys.exit(1)
client = OpenAI(api_key=OPENAI_API_KEY)
# Model
MODEL = os.getenv("UPGRADE_DATASET_MODEL", "gpt-4o-mini")
# System prompt

SYSTEM_PROMPT = """\
Bạn là trợ lý chuyên xử lý dữ liệu nha khoa. Nhiệm vụ:

1. **Chuyển nội dung sang Markdown**:
   - Dùng `- ` cho danh sách (KHÔNG dùng số thứ tự).
   - Dùng `**in đậm**` cho thuật ngữ y khoa quan trọng.
   - Giữ nguyên tất cả thông tin gốc, KHÔNG thêm bớt nội dung.
   - Tách đoạn hợp lý bằng dòng trống.

2. **Viết 1 câu summary** (tóm tắt) cực ngắn (tối đa 30 từ tiếng Việt) nắm bắt ý chính của bài.

Trả về JSON hợp lệ với đúng 2 trường:
{"summary": "...", "content_md": "..."}

KHÔNG trả về bất kỳ text nào ngoài JSON."""


# Hàm gọi OpenAI API
def call_openai(title: str, section: str, content: str, max_retries: int = 5) -> dict:
    """Gọi OpenAI API với retry logic khi gặp lỗi mạng/rate-limit."""
    # User message
    user_msg = (
        f"Tiêu đề: {title}\n"
        f"Mục: {section}\n"
        f"Nội dung:\n{content}"
    )

    # Retry logic
    for attempt in range(1, max_retries + 1):
        try:
            # Gọi OpenAI API
            resp = client.chat.completions.create(
                model=MODEL,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
            )
            # Lấy kết quả
            raw = resp.choices[0].message.content
            result = json.loads(raw)

            # Kiểm tra kết quả
            if "summary" not in result or "content_md" not in result:
                raise ValueError(f"Missing keys in response: {list(result.keys())}")

            # Trả về kết quả
            return result

        except (APITimeoutError, APIError, RateLimitError) as e:
            # Wait and retry
            wait = min(2 ** attempt, 60)
            print(f"\n  [Retry {attempt}/{max_retries}] {type(e).__name__}: {e}")
            print(f"  Đợi {wait}s rồi thử lại...")
            time.sleep(wait)

        except (json.JSONDecodeError, ValueError) as e:
            # Wait and retry
            wait = 2
            print(f"\n  [Retry {attempt}/{max_retries}] Parse error: {e}")
            time.sleep(wait)

    # Skip
    print(f"  SKIP: Không thể xử lý sau {max_retries} lần thử.")
    return None


# Hàm load kết quả đã xử lý trước đó (nếu có) để resume
def load_existing_progress(output_path: Path) -> list[dict]:
    """Load kết quả đã xử lý trước đó (nếu có) để resume."""
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_checkpoint(data: list[dict], path: Path) -> None:
    # Tạo thư mục nếu không tồn tại
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Hàm chính
def main():
    # Kiểm tra input path
    if not INPUT_PATH.exists():
        print(f"ERROR: Không tìm thấy {INPUT_PATH}")
        sys.exit(1)

    # Load dataset
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # Tổng số bài viết
    total = len(dataset)
    print(f"Loaded {total} tài liệu từ {INPUT_PATH}")

    # Load kết quả đã xử lý trước đó (nếu có) để resume
    results = load_existing_progress(OUTPUT_PATH)
    processed_ids = {item["id"] for item in results}

    if results:
        print(f"Resume: đã có {len(results)} tài liệu từ lần chạy trước, tiếp tục...")

    skipped = 0
    pbar = tqdm(dataset, desc="Upgrading", unit="tài liệu")

    for doc in pbar:
        doc_id = doc.get("id", "")

        if doc_id in processed_ids:
            pbar.set_postfix(status="skip (đã có)")
            continue

        title = doc.get("title", "")
        section = doc.get("section", "")
        content = doc.get("content", "")

        result = call_openai(title, section, content)

        if result is None:
            skipped += 1
            upgraded = {
                "id": doc_id,
                "title": title,
                "section": section,
                "summary": "",
                "content": content,
                "source": doc.get("source", ""),
                "source_name": doc.get("source_name", ""),
                "metadata": doc.get("metadata", {}),
            }
        else:
            upgraded = {
                "id": doc_id,
                "title": title,
                "section": section,
                "summary": result["summary"],
                "content": result["content_md"],
                "source": doc.get("source", ""),
                "source_name": doc.get("source_name", ""),
                "metadata": doc.get("metadata", {}),
            }

        results.append(upgraded)
        processed_ids.add(doc_id)

        if len(results) % CHECKPOINT_INTERVAL == 0:
            save_checkpoint(results, OUTPUT_PATH)
            pbar.set_postfix(saved=f"{len(results)}/{total}")

    save_checkpoint(results, OUTPUT_PATH)

    print(f"\n{'=' * 60}")
    print(f"  HOÀN TẤT!")
    print(f"  Tổng: {len(results)} tài liệu  |  Bỏ qua (lỗi): {skipped}")
    print(f"  Output: {OUTPUT_PATH}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
