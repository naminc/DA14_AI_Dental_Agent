import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
from src.agent.chatbot import DentalChatbot

st.set_page_config(
    page_title="Dental AI Chatbot",
    page_icon="medkit",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# CUSTOM CSS - PROFESSIONAL & MINIMALIST UI
# =========================================================
st.markdown(
    """
    <style>
    /* Ẩn nút Deploy rườm rà của Streamlit */
    .stAppDeployButton {display: none !important;}

    /* Nhúng Font Inter (Nghiêm túc, chuyên nghiệp) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* ===== Page & Background ===== */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }

    /* Main width - PADDING TOP ĐỂ NÉ HEADER */
    .block-container {
        max-width: 1200px;
        padding-top: 4.5rem; 
        padding-bottom: 5rem;
    }

    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    /* ===== ÉP PHẦN TỬ CUỐI Ở SIDEBAR XUỐNG ĐÁY ===== */
    div[data-testid="stSidebarUserContent"] div[data-testid="stVerticalBlock"] {
        min-height: calc(100vh - 6rem);
        display: flex;
        flex-direction: column;
    }
    
    div[data-testid="stSidebarUserContent"] div[data-testid="stVerticalBlock"] > div.element-container:last-child {
        margin-top: auto;
    }

    /* ===== Typography ===== */
    .hero-title {
        font-size: 2.2rem;
        line-height: 1.2;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }

    .hero-subtitle {
        font-size: 1rem;
        font-weight: 400;
        color: #475569;
        margin-bottom: 1.5rem;
    }

    .section-label {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }

    .tiny-muted {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 1rem;
        display: block;
    }

    /* ===== Cards & Containers ===== */
    .header-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.5rem 2rem;
    }

    .source-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }

    .source-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 0.5rem;
    }

    /* ===== Chips / Tags ===== */
    .chip {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
        border-radius: 4px;
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #cbd5e1;
        font-size: 0.75rem;
        font-weight: 500;
    }

    /* ===== Streamlit Chat Overrides ===== */
    div[data-testid="stChatMessage"] {
        background: transparent !important;
        padding: 0 !important;
        margin-bottom: 1.5rem !important;
        border: none !important;
    }

    /* ===== Chat Bubbles ===== */
    .chat-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .chat-row.user {
        flex-direction: row-reverse;
    }

    .avatar {
        width: 36px;
        height: 36px;
        min-width: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .avatar.ai {
        background: #0f172a;
        color: #ffffff;
    }

    .avatar.user {
        background: #e2e8f0;
        color: #0f172a;
    }

    .message-content {
        max-width: 80%;
    }

    .user-bubble {
        background: #f1f5f9;
        color: #0f172a;
        border-radius: 8px 8px 0 8px;
        padding: 0.85rem 1rem;
        font-size: 0.95rem;
        line-height: 1.5;
        border: 1px solid #e2e8f0;
    }

    .assistant-bubble {
        background: #ffffff;
        color: #1e293b;
        border-radius: 8px 8px 8px 0;
        padding: 0.85rem 1rem;
        font-size: 0.95rem;
        line-height: 1.6;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }

    /* ===== Buttons ===== */
    .stButton > button {
        width: 100%;
        border-radius: 6px !important;
        border: 1px solid #cbd5e1 !important;
        background: #ffffff !important;
        color: #0f172a !important;
        font-weight: 500 !important;
        padding: 0.4rem 0.8rem !important;
        transition: none !important;
    }

    .stButton > button:hover {
        border-color: #94a3b8 !important;
        background: #f8fafc !important;
        color: #0f172a !important;
    }

    /* ===== Info boxes & Empty States ===== */
    .nice-note {
        background: #f8fafc;
        border-left: 3px solid #64748b;
        color: #475569;
        padding: 0.75rem 1rem;
        font-size: 0.85rem;
        line-height: 1.5;
        margin-bottom: 1rem;
    }

    .empty-state {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        color: #64748b;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        font-size: 0.95rem;
    }

    /* ===== Expander ===== */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        color: #334155 !important;
        font-size: 0.9rem !important;
        padding-left: 0.5rem !important; 
    }
    
    div[data-testid="stExpander"] {
        border: none !important; 
        box-shadow: none !important;
        background-color: transparent !important;
    }

    h1, h2, h3 { margin-top: 0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# STATE INITIALIZATION
# =========================================================
if "bot" not in st.session_state:
    st.session_state.bot = DentalChatbot()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Thêm một biến trạng thái để lưu câu hỏi đang cần bot trả lời
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

def clear_chat():
    st.session_state.chat_history = []
    st.session_state.last_result = None
    st.session_state.pending_question = None

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("## Dental AI")
    st.markdown(
        '<span class="tiny-muted">Hệ thống RAG + FAISS + GPT</span>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Quản trị hệ thống")
    if st.button("Xóa lịch sử hội thoại", key="clear", use_container_width=True):
        clear_chat()

    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="nice-note">Lưu ý: Nội dung truy xuất từ cơ sở dữ liệu mang tính chất tham khảo, không thay thế chỉ định y khoa chính thức.</div>',
        unsafe_allow_html=True,
    )

# =========================================================
# HEADER
# =========================================================
st.markdown(
    """
    <div class="header-card">
        <div class="hero-title">Dental AI Chatbot</div>
        <div class="hero-subtitle">
            Hệ thống hỗ trợ tra cứu kiến thức nha khoa dựa trên mô hình ngôn ngữ lớn.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

# =========================================================
# MAIN LAYOUT
# =========================================================
left_col, right_col = st.columns([2.3, 1], gap="large")

# -------------------------
# LEFT: CHAT
# -------------------------
with left_col:
    st.markdown('<div class="section-label">Lịch sử hội thoại</div>', unsafe_allow_html=True)

    # Hiển thị rỗng nếu chưa có lịch sử VÀ chưa có câu hỏi nào đang xử lý
    if not st.session_state.chat_history and not st.session_state.pending_question:
        st.markdown(
            """
            <div class="empty-state">
                Hệ thống đang ở trạng thái chờ.<br>Vui lòng nhập câu hỏi từ thanh công cụ bên dưới.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # 1. Vẽ ra TOÀN BỘ lịch sử chat (bao gồm cả câu hỏi user vừa nhập)
        for msg in st.session_state.chat_history:
            content = msg["content"].replace("\n", "<br>")
            if msg["role"] == "user":
                st.markdown(
                    f"""
                    <div class="chat-row user">
                        <div class="avatar user">U</div>
                        <div class="message-content">
                            <div class="user-bubble">{content}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="chat-row">
                        <div class="avatar ai">AI</div>
                        <div class="message-content">
                            <div class="assistant-bubble">{content}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # 2. KIỂM TRA: Nếu có câu hỏi đang cần xử lý (pending_question)
        if st.session_state.pending_question:
            # Hiển thị icon load ngay dưới câu hỏi của user
            with st.spinner("AI đang phân tích và truy xuất dữ liệu..."):
                # Gọi Bot (truyền lịch sử chat cũ không bao gồm câu hỏi vừa đẩy vào)
                result = st.session_state.bot.answer(
                    user_question=st.session_state.pending_question,
                    chat_history=st.session_state.chat_history[:-1] 
                )
            
            # Lưu câu trả lời của Bot
            st.session_state.chat_history.append(
                {"role": "assistant", "content": result["answer"]}
            )
            st.session_state.last_result = result
            
            # Xóa trạng thái pending và tải lại UI một lần nữa để vẽ bong bóng chat của AI
            st.session_state.pending_question = None
            st.rerun()

# -------------------------
# RIGHT: RETRIEVAL PANEL
# -------------------------
with right_col:
    st.markdown('<div class="section-label">Thông tin truy xuất</div>', unsafe_allow_html=True)

    if st.session_state.last_result:
        result = st.session_state.last_result

        st.markdown("**Truy vấn gốc đã tối ưu:**")
        st.code(result["rewritten_query"], language=None)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Nguồn dữ liệu tham chiếu:**")
        
        for i, item in enumerate(result["sources"], start=1):
            title = item.get("title", "Không có tiêu đề")
            section = item.get("section", "Chung")
            disease = item.get("metadata", {}).get("disease", "N/A")
            topic = item.get("metadata", {}).get("topic", "N/A")
            source_name = item.get("source_name", "Không rõ")
            source_url = item.get("source", "#")
            content = item.get("content", "Không có nội dung")

            st.markdown(
                f"""
                <div class="source-box">
                    <div class="source-title">[{i}] {title} - {section}</div>
                    <span class="chip">Bệnh lý: {disease}</span>
                    <span class="chip">Chủ đề: {topic}</span>
                    <span class="chip">Nguồn: {source_name}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander(f"Nội dung văn bản (Chunk #{i})", expanded=False):
                st.write(content)
                st.markdown(f"[Mở tài liệu gốc]({source_url})")
    else:
        st.markdown(
            """
            <div class="empty-state" style="padding: 1.5rem 1rem;">
                Các tài liệu được trích xuất sẽ hiển thị tại đây sau khi hệ thống xử lý truy vấn.
            </div>
            """,
            unsafe_allow_html=True,
        )

# =========================================================
# CHAT INPUT (GHI NHẬN CÂU HỎI VÀ LƯU TRẠNG THÁI)
# =========================================================
user_input = st.chat_input("Nhập câu hỏi tại đây...")
if user_input:
    # 1. Đưa luôn câu hỏi của User vào lịch sử hiển thị
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    # 2. Đánh dấu câu hỏi này đang cần xử lý
    st.session_state.pending_question = user_input
    # 3. Tải lại trang ngay lập tức để Render câu hỏi ra màn hình
    st.rerun()