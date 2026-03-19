export const SUGGESTIONS = [
  "Sâu răng là gì?",
  "Cách chăm sóc răng sau khi niềng?",
  "Dấu hiệu sâu răng như thế nào?",
  "Làm sao để phòng ngừa hôi miệng?",
  "Sau khi nhổ răng nên ăn gì và kiêng gì?",
];

export const APP_CONFIG = {
  NAME: "Dental AI Assistant",
  VERSION: "1.0.0",
  API_URL: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
  DEVELOPER: "Ngo Dinh Nam",
  TECH_STACK: "Next.js, FastAPI, OpenAI, FAISS, Sentence-Transformers, Ollama, Python",
  DESCRIPTION: "Ứng dụng trợ lý nha khoa AI sử dụng công nghệ RAG (Retrieval-Augmented Generation) để cung cấp thông tin tư vấn sức khỏe răng miệng.",
};

export const UI_MESSAGES = {
  WELCOME_TITLE: "Tôi có thể giúp gì cho sức khỏe răng miệng của bạn?",
  WELCOME_SUBTITLE:
    "Hệ thống RAG được huấn luyện từ các tài liệu nha khoa chính thống.",
  ERROR_CONNECTION: "Không thể kết nối đến máy chủ. Vui lòng thử lại sau!",
};
