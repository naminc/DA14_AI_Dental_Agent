import os
import json
import sys
import dotenv
import time
import requests
import re
from bs4 import BeautifulSoup
from openai import OpenAI

dotenv.load_dotenv()

# ================= CẤU HÌNH =================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINKS_FILE = "links_test.txt"
OUTPUT_FILE = "data/test/dental_dataset.json"

client = OpenAI(api_key=OPENAI_API_KEY)

# ================= 1. HÀM CÀO DỮ LIỆU =================
def scrape_dental_article(url):
    print(f"\n[1/3] Đang cào: {url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Lỗi tải trang: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Dọn rác HTML
    for tag in soup.find_all(['script', 'style', 'header', 'footer', 'nav', 'aside', 'form']):
        tag.decompose()
    for noisy_div in soup.find_all('div', class_=re.compile(r'ad-|banner|sidebar|related|menu', re.I)):
        noisy_div.decompose()

    # Lấy tiêu đề và nội dung
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else soup.title.get_text(strip=True)
    
    main_content = soup.find('article') or soup.find('div', class_=re.compile(r'content|post', re.I)) or soup.body
    raw_text = main_content.get_text(separator='\n', strip=True)
    clean_text = re.sub(r'\n{3,}', '\n\n', raw_text)

    # Nếu bài quá ngắn (có thể bị chặn hoặc cào nhầm), bỏ qua
    if len(clean_text) < 200:
        print("Nội dung quá ngắn, bỏ qua trang này. 200 characters")
        return None

    # Lấy Tên nguồn (Ví dụ: nhakhoakim.com)
    source_name = url.split('/')[2].replace('www.', '')

    return {"url": url, "title": title, "text": clean_text, "source_name": source_name}

# ================= 2. HÀM GỌI AI ĐỂ FORMAT JSON =================
def extract_dental_data_to_json(scraped_data):
    print(f"[2/3] Gửi GPT phân tích bài: {scraped_data['title']}")
    
    prompt = f"""
Bạn là chuyên gia bóc tách dữ liệu y tế (Data Extraction Specialist). 
Hãy đọc bài viết dưới đây và chia nhỏ nó thành các mục logic y khoa (ví dụ: Khái niệm, Phân loại, Ưu nhược điểm, Quy trình, Chi tiết chi phí, Chăm sóc...).

QUY TẮC TRÍCH XUẤT VÀ LỌC NHIỄU (RẤT QUAN TRỌNG):
1. BỘ LỌC RÁC (NOISE FILTERING): Bỏ qua hoàn toàn, TUYỆT ĐỐI KHÔNG trích xuất các nội dung mang tính chất quảng cáo, thương mại hoặc hành chính như: Hình thức thanh toán, Trả góp, Chương trình khuyến mãi, Câu chuyện khách hàng, Lời tri ân, Đặt lịch hẹn, Địa chỉ phòng khám, Lời khuyên chọn nha khoa.
2. CHỈ TRÍCH XUẤT KIẾN THỨC Y KHOA: Chỉ lấy các thông tin về bệnh lý, phương pháp điều trị, quy trình thực hiện, ưu/nhược điểm, giá cả y tế chi tiết và hướng dẫn chăm sóc,....
3. KHÔNG tóm tắt quá ngắn. Key "content" phải chứa TOÀN BỘ nội dung chi tiết của mục đó (dài từ 100 đến 400 chữ).
4. NẾU bài gốc có liệt kê (bullet points, các bước), BẮT BUỘC phải giữ nguyên định dạng gạch đầu dòng đó trong "content".
5. Bóc tách thành một MẢNG (ARRAY) các JSON object nằm trong key "data".

Định dạng yêu cầu cho mỗi object:
{{
    "id": "tạo_id_slug_ngắn_gọn_kèm_nguồn_ví_dụ sau-rang-vinmec-01",
    "title": "{scraped_data['title']}",
    "section": "Tên mục (VD: Quy trình cấy Implant chuẩn y khoa)",
    "content": "GHI CHI TIẾT VÀ ĐẦY ĐỦ NỘI DUNG Ở ĐÂY. Giữ nguyên gạch đầu dòng.",
    "source": "{scraped_data['url']}",
    "source_name": "{scraped_data['source_name']}",
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
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "Trả về duy nhất 1 JSON object chứa key 'data' là mảng các mẩu tin y khoa. Đã lọc bỏ quảng cáo."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1 # Giữ ở 0.1 để AI tuân thủ nghiêm ngặt mệnh lệnh
        )
        
        result_json = json.loads(response.choices[0].message.content)
        return result_json.get("data", [])
    except Exception as e:
        print(f"Lỗi khi gọi GPT: {e}")
        return []

# ================= 3. LUỒNG CHẠY CHÍNH (PIPELINE) =================
def run_pipeline():
    # Bước 1: Đọc danh sách link
    if not os.path.exists(LINKS_FILE):
        print(f"Không tìm thấy file {LINKS_FILE}. Hãy tạo file này và cho link vào.")
        return

    with open(LINKS_FILE, 'r', encoding='utf-8') as f:
        links = [line.strip() for line in f if line.strip()]

    print(f"Tìm thấy {len(links)} link. Bắt đầu xử lý...")

    # Bước 2: Tải dữ liệu cũ lên (nếu có) để không bị ghi đè mất
    dataset = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            try:
                dataset = json.load(f)
                print(f"Đã load {len(dataset)} chunks cũ từ database.")
            except:
                pass

    # Bước 3: Duyệt từng link
    success_count = 0
    for idx, link in enumerate(links):
        print(f"\n--- Đang xử lý link {idx + 1}/{len(links)} ---")
        
        scraped_data = scrape_dental_article(link)
        if not scraped_data:
            continue
            
        chunks = extract_dental_data_to_json(scraped_data)
        
        if chunks:
            dataset.extend(chunks)
            success_count += 1
            print(f"[3/3] Trích xuất thành công {len(chunks)} chunks!")
            
            # AUTO-SAVE: Lưu lại ngay sau khi xử lý xong 1 link
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
        else:
            print("[3/3] Không trích xuất được chunk nào.")
            
        # Nghỉ 3 giây để tránh bị website hoặc OpenAI khóa IP vì spam requests
        time.sleep(3) 

    print(f"\nHOÀN TẤT! Đã xử lý thành công {success_count}/{len(links)} link.")
    print(f"Tổng số chunks hiện tại trong {OUTPUT_FILE}: {len(dataset)}")

if __name__ == "__main__":
    run_pipeline()