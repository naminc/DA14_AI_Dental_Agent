import type { Source } from "@/hooks/use-dental-chat";

// Type Definitions
interface ExportData {
  question: string;
  answer: string;
  sources?: Source[];
  date?: string;
}

// CSS Styles
const CSS = `
  @page { margin: 20mm 15mm; size: A4; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif;
    color: #1a1a1a; font-size: 13px; line-height: 1.65;
  }

  .header {
    text-align: center; border-bottom: 2px solid #2563eb;
    padding-bottom: 14px; margin-bottom: 20px;
  }
  .header h1 { font-size: 20px; color: #2563eb; margin-bottom: 2px; }
  .header .subtitle { font-size: 11px; color: #6b7280; }
  .header .date { font-size: 11px; color: #9ca3af; margin-top: 6px; }

  .section { margin-bottom: 18px; }
  .section-label {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    color: #2563eb; letter-spacing: 0.5px; margin-bottom: 6px;
  }
  .question-box {
    background: #eff6ff; border-left: 3px solid #2563eb;
    padding: 10px 14px; border-radius: 4px; font-weight: 500;
  }
  .answer-box {
    background: #f9fafb; border-left: 3px solid #10b981;
    padding: 10px 14px; border-radius: 4px; white-space: pre-wrap;
  }

  .sources { margin-top: 20px; border-top: 1px solid #e5e7eb; padding-top: 14px; }
  .sources h3 { font-size: 12px; color: #6b7280; margin-bottom: 8px; }
  .source-item {
    font-size: 11px; color: #4b5563; padding: 4px 0;
    border-bottom: 1px dotted #e5e7eb;
  }
  .source-item a { color: #2563eb; text-decoration: none; }

  .footer {
    margin-top: 30px; text-align: center;
    font-size: 10px; color: #9ca3af; border-top: 1px solid #e5e7eb;
    padding-top: 10px;
  }

  @media print {
    body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
`;

// Build Sources HTML
function buildSourcesHtml(sources: Source[]): string {
  const uniqueSources = sources.reduce<Source[]>((acc, src) => {
    if (!acc.some((s) => s.source === src.source && s.title === src.title)) {
      acc.push(src);
    }
    return acc;
  }, []);

  const items = uniqueSources
    .map(
      (src, i) =>
        `<div class="source-item">
          [${i + 1}] <strong>${src.title || "Tài liệu"}</strong>
          ${src.section ? `— ${src.section}` : ""}
          ${src.source ? `<br/><a href="${src.source}">${src.source}</a>` : ""}
        </div>`
    )
    .join("");

  return `<div class="sources"><h3>Nguồn tham chiếu</h3>${items}</div>`;
}

// Export Consultation PDF
export function exportConsultationPdf({
  question,
  answer,
  sources,
  date,
}: ExportData): void {
  const now = date || new Date().toLocaleDateString("vi-VN", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });

  const html = `<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8"/>
  <title>Tư vấn Nha khoa — ${now}</title>
  <style>${CSS}</style>
</head>
<body>
  <div class="header">
    <h1>Phiếu Tư Vấn Nha Khoa</h1>
    <div class="subtitle">Được tạo bởi Dental AI Assistant</div>
    <div class="date">${now}</div>
  </div>

  <div class="section">
    <div class="section-label">Câu hỏi của bệnh nhân</div>
    <div class="question-box">${escapeHtml(question)}</div>
  </div>

  <div class="section">
    <div class="section-label">Nội dung tư vấn</div>
    <div class="answer-box">${escapeHtml(answer)}</div>
  </div>

  ${sources && sources.length > 0 ? buildSourcesHtml(sources) : ""}

  <div class="footer">
    Tài liệu này chỉ mang tính tham khảo, không thay thế tư vấn trực tiếp từ bác sĩ nha khoa.
  </div>
</body>
</html>`;

  const printWindow = window.open("", "_blank");
  if (!printWindow) return;

  printWindow.document.write(html);
  printWindow.document.close();
  printWindow.addEventListener("load", () => {
    printWindow.print();
  });
}

// Escape HTML
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
