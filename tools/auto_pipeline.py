"""
tools/auto_pipeline.py

Pipeline trích xuất dữ liệu nha khoa — hỗ trợ 2 chế độ:

  Cách 1 — raw:   Đọc bài viết từ file .txt trong folder tools/raw/
  Cách 2 — crawl:  Cào bài viết từ danh sách link

Chạy:
  python tools/auto_pipeline.py --mode raw
  python tools/auto_pipeline.py --mode crawl
  python tools/auto_pipeline.py --mode raw  --raw-dir raw --output data/test/dental_dataset.json
  python tools/auto_pipeline.py --mode crawl --links links/test.txt --output data/test/dental_dataset.json
"""

import os
import json
import sys
import argparse
import glob
import time
import re

import dotenv
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ────────────────────────────────────────────
# Shared: GPT chunking
# ────────────────────────────────────────────

def _slugify(text):
    """Chuyển text tiếng Việt thành slug ASCII cho id."""
    import unicodedata
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[đĐ]", "d", text)
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:50]


def _make_source_slug(source_name):
    """Rút gọn source_name thành slug ngắn (vd: 'nhathuoclongchau.com.vn' → 'nhathuoclongchau')."""
    return source_name.split(".")[0]


def extract_dental_data_to_json(scraped_data):
    """Gửi GPT phân tích bài viết → trả về danh sách chunks JSON (id được tự sinh trong code)."""
    print(f"  [GPT] Đang phân tích: {scraped_data['title']}")

    prompt = f"""
Bạn là chuyên gia bóc tách dữ liệu y tế (Data Extraction Specialist). 
Hãy đọc bài viết dưới đây và chia nhỏ nó thành các mục logic y khoa (ví dụ: Khái niệm, Phân loại, Ưu nhược điểm, Quy trình, Chi tiết chi phí, Chăm sóc...).

QUY TẮC TRÍCH XUẤT VÀ LỌC NHIỄU (RẤT QUAN TRỌNG):
1. BỘ LỌC RÁC (NOISE FILTERING): Bỏ qua hoàn toàn, TUYỆT ĐỐI KHÔNG trích xuất các nội dung mang tính chất quảng cáo, thương mại hoặc hành chính như: Hình thức thanh toán, Trả góp, Chương trình khuyến mãi, Câu chuyện khách hàng, Lời tri ân, Đặt lịch hẹn, Địa chỉ phòng khám, Lời khuyên chọn nha khoa.
2. CHỈ TRÍCH XUẤT KIẾN THỨC Y KHOA: Chỉ lấy các thông tin về bệnh lý, phương pháp điều trị, quy trình thực hiện, ưu/nhược điểm, giá cả y tế chi tiết và hướng dẫn chăm sóc,....
3. KHÔNG tóm tắt quá ngắn. Key "content" phải chứa TOÀN BỘ nội dung chi tiết của mục đó (dài từ 100 đến 400 chữ).
4. NẾU bài gốc có liệt kê (bullet points, các bước), BẮT BUỘC phải giữ nguyên định dạng gạch đầu dòng đó trong "content".
5. Bóc tách thành một MẢNG (ARRAY) các JSON object nằm trong key "data".
6. KHÔNG TỰ TẠO trường "id" — hệ thống sẽ tự sinh id. Chỉ cần trả về các trường: title, section, content, metadata.

Định dạng yêu cầu cho mỗi object:
{{
    "title": "{scraped_data['title']}",
    "section": "Tên mục (VD: Quy trình cấy Implant chuẩn y khoa)",
    "content": "GHI CHI TIẾT VÀ ĐẦY ĐỦ NỘI DUNG Ở ĐÂY. Giữ nguyên gạch đầu dòng.",
    "metadata": {{
        "source": "{scraped_data['source_name']}",
        "disease": "Tên bệnh/phương pháp chính",
        "topic": "Phân loại chủ đề (VD: khái niệm, phân loại, quy trình, chi phí, chăm sóc,...)"
    }}
}}

Bài viết gốc:
{scraped_data['text'][:8000]}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Trả về duy nhất 1 JSON object chứa key 'data' là mảng các mẩu tin y khoa. Đã lọc bỏ quảng cáo."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )
        result_json = json.loads(response.choices[0].message.content)
        chunks = result_json.get("data", [])

        # Tự sinh id + gắn source/source_name, đảm bảo thứ tự key chuẩn
        source_slug = _make_source_slug(scraped_data["source_name"])
        result = []
        for idx, chunk in enumerate(chunks, start=1):
            disease_slug = _slugify(chunk.get("metadata", {}).get("disease", ""))
            section_slug = _slugify(chunk.get("section", "chunk"))
            id_parts = [p for p in [disease_slug, section_slug, source_slug, f"{idx:02d}"] if p]
            result.append({
                "id": "-".join(id_parts),
                "title": chunk.get("title", ""),
                "section": chunk.get("section", ""),
                "content": chunk.get("content", ""),
                "source": scraped_data["url"],
                "source_name": scraped_data["source_name"],
                "metadata": chunk.get("metadata", {}),
            })

        return result
    except Exception as e:
        print(f"  [LỖI GPT] {e}")
        return []


# ────────────────────────────────────────────
# Mode 1: RAW — đọc từ file .txt
# ────────────────────────────────────────────

def parse_raw_file(filepath):
    """
    Đọc 1 file .txt, tách các bài viết.

    Format: mỗi bài cách nhau bởi 1 dòng trống.
    Mỗi bài: dòng 1 = URL, dòng 2 = title, dòng 3+ = nội dung.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"\n\s*\n", content.strip())
    articles = []

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue

        url = lines[0].strip()
        if not url.startswith("http"):
            continue

        title = lines[1].strip()
        text = "\n".join(lines[2:]).strip()

        if len(text) < 100:
            print(f"  [BỎ QUA] Nội dung quá ngắn (<100 ký tự): {title}")
            continue

        source_name = url.split("/")[2].replace("www.", "")
        articles.append({
            "url": url,
            "title": title,
            "text": text,
            "source_name": source_name,
        })

    return articles


def run_raw_pipeline(raw_dir, output_file):
    """Đọc tất cả file .txt trong raw_dir → GPT chunking → lưu JSON."""
    txt_files = sorted(glob.glob(os.path.join(raw_dir, "*.txt")))

    if not txt_files:
        print(f"Không tìm thấy file .txt nào trong {raw_dir}")
        return

    print(f"Tìm thấy {len(txt_files)} file .txt trong {raw_dir}:")
    for f in txt_files:
        print(f"  - {os.path.basename(f)}")

    # Đọc tất cả bài viết từ các file raw
    all_articles = []
    for filepath in txt_files:
        filename = os.path.basename(filepath)
        articles = parse_raw_file(filepath)
        print(f"\n[RAW] {filename}: {len(articles)} bài viết")
        all_articles.extend(articles)

    print(f"\nTổng cộng: {len(all_articles)} bài viết từ raw files.")

    if not all_articles:
        print("Không có bài viết nào để xử lý.")
        return

    # Load dataset cũ (nếu có)
    dataset = _load_existing_dataset(output_file)

    # GPT chunking từng bài
    success_count = 0
    for idx, article in enumerate(all_articles):
        print(f"\n--- [{idx + 1}/{len(all_articles)}] {article['title'][:60]} ---")

        chunks = extract_dental_data_to_json(article)

        if chunks:
            dataset.extend(chunks)
            success_count += 1
            print(f"  [OK] Trích xuất {len(chunks)} chunks")
            _save_dataset(dataset, output_file)
        else:
            print(f"  [SKIP] Không trích xuất được chunk nào.")

        time.sleep(2)

    _print_summary(success_count, len(all_articles), output_file, len(dataset))


# ────────────────────────────────────────────
# Mode 2: CRAWL — cào từ link
# ────────────────────────────────────────────

def scrape_dental_article(url):
    """Cào nội dung bài viết từ URL."""
    print(f"  [CRAWL] Đang cào: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"  [LỖI] Không tải được trang: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup.find_all(["script", "style", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()
    for noisy_div in soup.find_all("div", class_=re.compile(r"ad-|banner|sidebar|related|menu", re.I)):
        noisy_div.decompose()

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else soup.title.get_text(strip=True)

    main_content = soup.find("article") or soup.find("div", class_=re.compile(r"content|post", re.I)) or soup.body
    raw_text = main_content.get_text(separator="\n", strip=True)
    clean_text = re.sub(r"\n{3,}", "\n\n", raw_text)

    if len(clean_text) < 200:
        print("  [BỎ QUA] Nội dung quá ngắn (<200 ký tự)")
        return None

    source_name = url.split("/")[2].replace("www.", "")
    return {"url": url, "title": title, "text": clean_text, "source_name": source_name}


def run_crawl_pipeline(links_file, output_file):
    """Cào link → GPT chunking → lưu JSON."""
    if not os.path.exists(links_file):
        print(f"Không tìm thấy file {links_file}. Hãy tạo file này và cho link vào.")
        return

    with open(links_file, "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]

    print(f"Tìm thấy {len(links)} link. Bắt đầu xử lý...")

    dataset = _load_existing_dataset(output_file)

    success_count = 0
    for idx, link in enumerate(links):
        print(f"\n--- [{idx + 1}/{len(links)}] ---")

        scraped_data = scrape_dental_article(link)
        if not scraped_data:
            continue

        chunks = extract_dental_data_to_json(scraped_data)

        if chunks:
            dataset.extend(chunks)
            success_count += 1
            print(f"  [OK] Trích xuất {len(chunks)} chunks")
            _save_dataset(dataset, output_file)
        else:
            print(f"  [SKIP] Không trích xuất được chunk nào.")

        time.sleep(3)

    _print_summary(success_count, len(links), output_file, len(dataset))


# ────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────

def _load_existing_dataset(output_file):
    """Load dataset cũ (nếu có) để nối tiếp."""
    dataset = []
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                dataset = json.load(f)
            print(f"Đã load {len(dataset)} chunks cũ từ {output_file}")
        except (json.JSONDecodeError, ValueError):
            pass
    return dataset


def _save_dataset(dataset, output_file):
    """Lưu dataset ra file JSON (auto-save sau mỗi bài)."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)


def _print_summary(success_count, total, output_file, total_chunks):
    print(f"\n{'=' * 50}")
    print(f"  HOÀN TẤT! {success_count}/{total} bài viết đã xử lý thành công.")
    print(f"  Tổng chunks trong {output_file}: {total_chunks}")
    print(f"{'=' * 50}")


# ────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline trích xuất dữ liệu nha khoa (raw hoặc crawl).",
        epilog=(
            "Ví dụ:\n"
            "  python tools/auto_pipeline.py --mode raw\n"
            "  python tools/auto_pipeline.py --mode crawl\n"
            "  python tools/auto_pipeline.py --mode raw  --raw-dir raw --output data/main/dental_dataset.json\n"
            "  python tools/auto_pipeline.py --mode crawl --links links/test.txt\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--mode",
        choices=["raw", "crawl"],
        required=True,
        help="Chế độ: 'raw' = đọc từ file .txt trong folder raw, 'crawl' = cào từ danh sách link",
    )
    parser.add_argument(
        "--raw-dir",
        default="raw",
        help="Thư mục chứa file .txt (chỉ dùng với --mode raw, mặc định: raw)",
    )
    parser.add_argument(
        "--links",
        default="links/test.txt",
        help="File chứa danh sách link (chỉ dùng với --mode crawl, mặc định: links/test.txt)",
    )
    parser.add_argument(
        "--output",
        default="data/test/dental_dataset.json",
        help="File output JSON (mặc định: data/test/dental_dataset.json)",
    )

    args = parser.parse_args()

    print(f"\n{'=' * 50}")
    print(f"  CHẾ ĐỘ: {args.mode.upper()}")
    print(f"  OUTPUT:  {args.output}")

    if args.mode == "raw":
        print(f"  RAW DIR: {args.raw_dir}")
        print(f"{'=' * 50}\n")
        run_raw_pipeline(args.raw_dir, args.output)
    else:
        print(f"  LINKS:   {args.links}")
        print(f"{'=' * 50}\n")
        run_crawl_pipeline(args.links, args.output)


if __name__ == "__main__":
    main()
