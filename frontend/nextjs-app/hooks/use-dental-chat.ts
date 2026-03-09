"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/use-auth-store";
import { useThemeStore } from "@/stores/use-theme-store";
import { APP_CONFIG, UI_MESSAGES } from "@/lib/constants";
import {
  validateToken,
  validateChatInput,
  confirmAction,
} from "@/lib/validators";

// ==========================================
// TYPE DEFINITIONS
// ==========================================
export interface Source {
  title: string;
  section: string;
  content: string;
  source: string;
  metadata: {
    disease: string;
    topic: string;
  };
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  rewrittenQuery?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
}

const API_BASE_URL = `${APP_CONFIG.API_URL}`;

// ==========================================
// CUSTOM HOOK — Chat logic only
// ==========================================
export function useDentalChat() {
  const router = useRouter();
  const { initialize, clearToken, fetchProfile } = useAuthStore();
  const user = useAuthStore((s) => s.user);
  const { isDark, toggleTheme, initialize: initTheme } = useThemeStore();

  const [input, setInput] = useState("");
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [openSources, setOpenSources] = useState<Record<number, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;
  const currentMessages = activeSession?.messages || [];

  // Load sessions from database and check auth
  useEffect(() => {
    const fetchSessions = async () => {
      const currentToken = initialize();
      if (!currentToken) {
        router.push("/login");
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
          headers: { Authorization: `Bearer ${currentToken}` },
        });
        if (response.ok) {
          const data = await response.json();
          setSessions(data);
        } else if (response.status === 401) {
          clearToken();
          router.push("/login");
          return;
        }
      } catch (error) {
        console.error("Lỗi tải lịch sử:", error);
      }

      // Load theme
      initTheme();

      // Load user profile if not cached
      fetchProfile();
      setIsCheckingAuth(false);
    };
    fetchSessions();
  }, [router, initialize, clearToken, initTheme]);

  // Auto-scroll when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentMessages.length]);

  // Reset open sources when switching session
  useEffect(() => {
    setOpenSources({});
  }, [activeSessionId]);

  // Create new chat
  const handleNewChat = useCallback(() => {
    setActiveSessionId(null);
    setInput("");
  }, []);

  // Select a session and load its messages from DB
  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      setActiveSessionId(sessionId);
      const currentToken = validateToken(router, clearToken);
      if (!currentToken) return;

      // If session has no messages loaded yet, fetch from API
      const currentSess = sessions.find((s) => s.id === sessionId);
      if (
        currentSess &&
        (!currentSess.messages || currentSess.messages.length === 0)
      ) {
        try {
          const res = await fetch(
            `${API_BASE_URL}/chat/sessions/${sessionId}/messages`,
            {
              headers: { Authorization: `Bearer ${currentToken}` },
            },
          );
          if (res.ok) {
            const msgs = await res.json();
            setSessions((prev) =>
              prev.map((s) =>
                s.id === sessionId ? { ...s, messages: msgs } : s,
              ),
            );
          }
        } catch (e) {
          console.error("Lỗi load tin nhắn chi tiết:", e);
        }
      }
    },
    [sessions, router, clearToken],
  );

  // Xóa một phiên chat cụ thể
  const handleDeleteSession = useCallback(
    async (e: React.MouseEvent, id: string) => {
      e.stopPropagation();

      const currentToken = validateToken(router, clearToken);
      if (!currentToken) return;

      if (!confirmAction("Bạn có chắc chắn muốn xóa cuộc trò chuyện này?"))
        return;

      try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${currentToken}` },
        });

        if (response.ok) {
          setSessions((prev) => prev.filter((s) => s.id !== id));
          if (activeSessionId === id) {
            setActiveSessionId(null);
          }
        } else {
          alert("Không thể xóa cuộc trò chuyện. Vui lòng thử lại.");
        }
      } catch (error) {
        console.error("Lỗi xóa session:", error);
      }
    },
    [activeSessionId, router, clearToken],
  );

  // Xóa sạch toàn bộ lịch sử
  const handleClearAllChat = useCallback(async () => {
    const currentToken = validateToken(router, clearToken);
    if (!currentToken) return;

    if (
      !confirmAction(
        "Hành động này sẽ xóa vĩnh viễn toàn bộ lịch sử chat. Bạn có chắc không?",
      )
    )
      return;

    try {
      const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${currentToken}` },
      });

      if (response.ok) {
        setSessions([]);
        setActiveSessionId(null);
        setOpenSources({});
      }
    } catch (e) {
      console.error("Lỗi xóa tất cả sessions:", e);
    }
  }, [router, clearToken]);

  // Handle submit với Streaming Response
  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      if (e) e.preventDefault();
      if (!validateChatInput(input, isLoading)) return;

      const currentToken = validateToken(router, clearToken);
      if (!currentToken) return;

      const userMessage: Message = { role: "user", content: input.trim() };
      let sessionId = activeSessionId;

      // 1. Cập nhật UI ngay lập tức với tin nhắn người dùng và tin nhắn trống của AI
      if (!sessionId) {
        sessionId = crypto.randomUUID();
        const newSession: ChatSession = {
          id: sessionId,
          title:
            userMessage.content.slice(0, 30) +
            (userMessage.content.length > 30 ? "..." : ""),
          messages: [userMessage, { role: "assistant", content: "" }], // Thêm AI placeholder
          updatedAt: Date.now(),
        };
        setSessions((prev) => [newSession, ...prev]);
        setActiveSessionId(sessionId);
      } else {
        setSessions((prev) =>
          prev.map((s) =>
            s.id === sessionId
              ? {
                  ...s,
                  messages: [
                    ...(s.messages || []),
                    userMessage,
                    { role: "assistant", content: "" }, // Thêm AI placeholder
                  ],
                }
              : s,
          ),
        );
      }

      const currentHistory = activeSession?.messages || [];
      setInput("");
      setIsLoading(true);

      try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${currentToken}`,
          },
          body: JSON.stringify({
            session_id: sessionId,
            user_question: userMessage.content,
            chat_history: currentHistory.map((m) => ({
              role: m.role,
              content: m.content,
            })),
          }),
        });

        if (!response.ok) {
          if (response.status === 401) {
            clearToken();
            router.push("/login");
            return;
          }
          throw new Error(`API error: ${response.status}`);
        }

        // 2. Bắt đầu đọc luồng Stream
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let accumulatedAnswer = "";
        let buffer = ""; // Dùng buffer để nối các gói tin bị cắt dở

        while (true) {
          const { done, value } = await reader!.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");

          // Giữ lại dòng cuối cùng (có thể chưa hoàn chỉnh) trong buffer
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.slice(6);
              if (!dataStr.trim()) continue;

              try {
                const data = JSON.parse(dataStr);

                // Nếu là Text Chunk -> Cộng dồn và cập nhật UI
                if (data.token) {
                  accumulatedAnswer += data.token;
                  setSessions((prev) =>
                    prev.map((s) => {
                      if (s.id !== sessionId) return s;
                      const msgs = [...(s.messages || [])];
                      const lastMsg = msgs[msgs.length - 1];
                      if (lastMsg && lastMsg.role === "assistant") {
                        msgs[msgs.length - 1] = {
                          ...lastMsg,
                          content: accumulatedAnswer,
                        };
                      }
                      return { ...s, messages: msgs, updatedAt: Date.now() };
                    }),
                  );
                } 
                // Nếu là tín hiệu kết thúc -> Cập nhật Sources và Metadata
                else if (data.done) {
                  setSessions((prev) =>
                    prev.map((s) => {
                      if (s.id !== sessionId) return s;
                      const msgs = [...(s.messages || [])];
                      const lastMsg = msgs[msgs.length - 1];
                      if (lastMsg && lastMsg.role === "assistant") {
                        msgs[msgs.length - 1] = {
                          ...lastMsg,
                          sources: data.sources,
                          rewrittenQuery: data.rewritten_query,
                        };
                      }
                      return { ...s, messages: msgs, updatedAt: Date.now() };
                    }),
                  );
                }
              } catch (e) {
                console.error("Lỗi parse JSON chunk:", e, dataStr);
              }
            }
          }
        }
      } catch (error) {
        console.error("Lỗi Stream:", error);
        // Fallback hiển thị lỗi
        setSessions((prev) =>
          prev.map((s) => {
            if (s.id !== sessionId) return s;
            const msgs = [...(s.messages || [])];
            msgs[msgs.length - 1] = {
              role: "assistant",
              content: UI_MESSAGES.ERROR_CONNECTION,
            };
            return { ...s, messages: msgs };
          }),
        );
      } finally {
        setIsLoading(false);
      }
    },
    [input, isLoading, activeSessionId, activeSession, router, clearToken],
  );

  // Logout → delegates to authStore
  const handleLogout = useCallback(() => {
    clearToken();
    router.push("/login");
  }, [router, clearToken]);

  return {
    // State
    input,
    setInput,
    sessions,
    activeSessionId,
    activeSession,
    currentMessages,
    isLoading,
    isCheckingAuth,
    isDark,
    openSources,
    setOpenSources,
    messagesEndRef,
    user,

    // Actions
    toggleTheme,
    handleNewChat,
    handleSelectSession,
    handleDeleteSession,
    handleClearAllChat,
    handleSubmit,
    handleLogout,
  };
}