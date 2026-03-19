import time
from ddgs import DDGS

# Các domain ưu tiên lấy bài viết nha khoa
TRUSTED_DOMAINS = [
    "vinmec.com",
    "elitedental.com.vn",
    "hellobacsi.com",
    "colgate.com.vn",
    "tamanhhospital.vn",
    "nhathuoclongchau.com.vn",
    "pharmacity.vn",
    "nhakhoatamducsmile.com",
    "nhakhoakim.com",
    "nhakhoaident.com",
    "nhakhoaparkway.com",
]

# Danh sách từ khóa nha khoa 
KEYWORDS = [
    # 1. BỆNH LÝ RĂNG MIỆNG (Oral Pathology)
    "nguyên nhân sâu răng",
    "điều trị viêm tủy răng",
    "viêm nha chu",
    "áp xe răng",
    "chảy máu chân răng",
    "tụt lợi",
    "hôi miệng nha khoa",
    "răng nhạy cảm ê buốt",
    "nhiệt miệng",
    "viêm nướu trùm",

    # 2. PHỤC HÌNH RĂNG (Restorative & Prosthodontics)
    "cấy ghép implant",
    "quy trình trồng răng implant",
    "bọc răng sứ thẩm mỹ",
    "dán sứ veneer",
    "cầu răng sứ",
    "hàm giả tháo lắp",
    "biến chứng bọc răng sứ",

    # 3. CHỈNH NHA (Orthodontics)
    "niềng răng mắc cài kim loại",
    "niềng răng trong suốt invisalign",
    "niềng răng mắc cài sứ",
    "độ tuổi niềng răng",
    "nong hàm niềng răng",
    "hàm duy trì sau niềng",

    # 4. NHA KHOA TỔNG QUÁT & PHÒNG NGỪA (General & Preventive)
    "nhổ răng khôn số 8",
    "biến chứng nhổ răng khôn",
    "trám răng thẩm mỹ",
    "cạo vôi răng lấy cao răng",
    "tẩy trắng răng",
    "hướng dẫn chăm sóc răng miệng",
    "dùng chỉ nha khoa đúng cách",
    "tăm nước nha khoa",

    # 5. NHA KHOA TRẺ EM (Pediatric Dentistry)
    "sâu răng trẻ em",
    "nhổ răng sữa cho bé",
    "tiền chỉnh nha cho trẻ"
]

# Các pattern URL bị loại bỏ
SKIP_PATTERNS = ["/tag/", "/category/", "/page/", "/author/", "/search/", "?s=", "/lien-he/", "/chu-de/", "/co-so-y-te/"]


def get_links(num_results_per_query=30, output_file="tools/links.txt"):
    all_links = []
    seen = set()

    # 1. TỰ ĐỘNG TẠO MA TRẬN TÌM KIẾM (Domain x Keyword)
    queries = []
    for domain in TRUSTED_DOMAINS:
        for keyword in KEYWORDS:
            queries.append(f"site:{domain} {keyword}")

    print(f"Đã tạo {len(queries)} câu lệnh tìm kiếm. Bắt đầu thu thập...\n")

    with DDGS() as ddgs:
        for idx, query in enumerate(queries):
            print(f"[{idx+1}/{len(queries)}] Đang tìm: '{query}'...")
            try:
                # Tăng max_results lên để lấy sâu hơn
                results = ddgs.text(query, region="vn-vi", max_results=num_results_per_query)
                count = 0
                
                # Nếu DDGS trả về None (do lỗi hoặc hết kết quả)
                if not results:
                    print("  => Không có kết quả nào.")
                    time.sleep(2)
                    continue

                for r in results:
                    url = r.get("href", "")

                    # Bỏ qua nếu đã có hoặc không phải URL hợp lệ
                    if url in seen or not url:
                        continue

                    # Bỏ qua các URL rác (tag, category...)
                    if any(p in url for p in SKIP_PATTERNS):
                        continue

                    all_links.append(url)
                    seen.add(url)
                    count += 1
                    print(f"  + {url}")

                print(f"  => Lấy được {count} link\n")

            except Exception as e:
                print(f"  Lỗi với query '{query}': {e}\n")

            # Nghỉ 2-3 giây giữa các lần query để tránh bị DuckDuckGo block IP
            time.sleep(3)

    # 2. GHI KẾT QUẢ RA FILE
    with open(output_file, "w", encoding="utf-8") as f:
        for link in all_links:
            f.write(link + "\n")

    print(f"HOÀN TẤT! Tổng cộng {len(all_links)} link duy nhất đã được lưu vào {output_file}.")


if __name__ == "__main__":
    # Nâng num_results_per_query lên 30 hoặc 50 để lấy nhiều bài hơn cho mỗi từ khóa
    get_links(num_results_per_query=30, output_file="links.txt")