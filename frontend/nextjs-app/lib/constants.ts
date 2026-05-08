// Suggestions
export const SUGGESTIONS = [
  "Sâu răng là gì?",
  "Viêm nướu là gì?",
  "Cách chăm sóc răng sau khi niềng?",
  "Dấu hiệu sâu răng như thế nào?",
  "Làm sao để phòng ngừa hôi miệng?",
  "Sau khi nhổ răng nên ăn gì và kiêng gì?",
];

// App Configuration
export const APP_CONFIG = {
  NAME: "Dental AI Assistant",
  VERSION: "1.0.0",
  API_URL: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
  DEVELOPER: "Ngo Dinh Nam",
  EMAIL: "admin@naminc.dev",
  PHONE: "0347101143",
  ADDRESS: "12 Linh Dong, Thu Duc, TP.HCM",
  TECH_STACK: "Next.js, FastAPI, OpenAI, FAISS, Sentence-Transformers, Ollama, Python",
  DESCRIPTION: "Ứng dụng trợ lý nha khoa AI sử dụng công nghệ RAG (Retrieval-Augmented Generation) để cung cấp thông tin tư vấn sức khỏe răng miệng.",
  YEAR: new Date().getFullYear(),
};

// UI Messages
export const UI_MESSAGES = {
  WELCOME_TITLE: "Tôi có thể giúp gì cho sức khỏe răng miệng của bạn?",
  WELCOME_SUBTITLE:
    "Hệ thống RAG được huấn luyện từ các tài liệu nha khoa chính thống.",
  ERROR_CONNECTION: "Không thể kết nối đến máy chủ. Vui lòng thử lại sau!",
  DISCLAIMER: "Thông tin chỉ mang tính tham khảo, không thay thế tư vấn trực tiếp từ bác sĩ nha khoa.",
  SIDEBAR_NOTE_DISCLAIMER: "Nội dung truy xuất mang tính tham khảo, không thay thế chỉ định y khoa chính thức từ bác sĩ.",
};
