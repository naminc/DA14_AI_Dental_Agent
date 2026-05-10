"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/use-auth-store";
import { useThemeStore } from "@/stores/use-theme-store";
import { APP_CONFIG, UI_MESSAGES } from "@/lib/constants";
import { validateToken, validateChatInput, confirmAction } from "@/lib/validators";
import { readChatStream } from "@/lib/stream-reader";

// Type Definitions
export interface Source {
  id: string;
  title: string;
  section: string;
  summary: string;
  content: string;
  source: string;
  source_name: string;
  metadata: {
    disease: string;
    source: string;
    topic: string;
  };
}

// Message Type
export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  rewrittenQuery?: string;
}

// Chat Session Type
export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
}

// API Base URL
const API_BASE_URL = `${APP_CONFIG.API_URL}`;

// Dental Chat Hook
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
  const [isAboutOpen, setIsAboutOpen] = useState(false);
  const [isAccountOpen, setIsAccountOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;
  const currentMessages = activeSession?.messages || [];

  // Fetch sessions from database and check authentication
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

      initTheme();
      fetchProfile();
      setIsCheckingAuth(false);
    };
    fetchSessions();
  }, [router, initialize, clearToken, initTheme]);

  // Auto scroll when new message is added
  const lastMessageContent = currentMessages[currentMessages.length - 1]?.content ?? "";
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: isLoading ? "auto" : "smooth",
      block: "end",
    });
  }, [currentMessages.length, lastMessageContent, isLoading]);

  useEffect(() => {
    setOpenSources({});
  }, [activeSessionId]);

  // Create new session
  const handleNewChat = useCallback(() => {
    setActiveSessionId(null);
    setInput("");
  }, []);

  // Select a session
  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      setActiveSessionId(sessionId);
      const currentToken = validateToken(router, clearToken);
      if (!currentToken) return;

      const session = sessions.find((s) => s.id === sessionId);
      if (session && (!session.messages || session.messages.length === 0)) {
        try {
          const res = await fetch(
            `${API_BASE_URL}/chat/sessions/${sessionId}/messages`,
            { headers: { Authorization: `Bearer ${currentToken}` } },
          );
          if (res.ok) {
            const msgs = await res.json();
            setSessions((prev) =>
              prev.map((s) => (s.id === sessionId ? { ...s, messages: msgs } : s)),
            );
          }
        } catch (e) {
          console.error("Lỗi load tin nhắn chi tiết:", e);
        }
      }
    },
    [sessions, router, clearToken],
  );

  // Delete a specific session
  const handleDeleteSession = useCallback(
    async (e: React.MouseEvent, id: string) => {
      e.stopPropagation();
      const currentToken = validateToken(router, clearToken);
      if (!currentToken) return;
      if (!confirmAction("Bạn có chắc chắn muốn xóa cuộc trò chuyện này?")) return;

      try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${currentToken}` },
        });

        if (response.ok) {
          setSessions((prev) => prev.filter((s) => s.id !== id));
          if (activeSessionId === id) setActiveSessionId(null);
        } else {
          alert("Không thể xóa cuộc trò chuyện. Vui lòng thử lại.");
        }
      } catch (error) {
        console.error("Lỗi xóa session:", error);
      }
    },
    [activeSessionId, router, clearToken],
  );

  // Delete all sessions
  const handleClearAllChat = useCallback(async () => {
    const currentToken = validateToken(router, clearToken);
    if (!currentToken) return;
    if (!confirmAction("Hành động này sẽ xóa vĩnh viễn toàn bộ lịch sử chat. Bạn có chắc không?")) return;

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

  // Update last assistant message
  const updateLastAssistantMessage = useCallback(
    (sessionId: string, updater: (msg: Message) => Message) => {
      setSessions((prev) =>
        prev.map((s) => {
          if (s.id !== sessionId) return s;
          const msgs = [...(s.messages || [])];
          const last = msgs[msgs.length - 1];
          if (last?.role === "assistant") msgs[msgs.length - 1] = updater(last);
          return { ...s, messages: msgs, updatedAt: Date.now() };
        }),
      );
    },
    [],
  );

  // Handle submit with stream
  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      if (e) e.preventDefault();
      if (!validateChatInput(input, isLoading)) return;

      const currentToken = validateToken(router, clearToken);
      if (!currentToken) return;

      const userMessage: Message = { role: "user", content: input.trim() };
      let sessionId = activeSessionId;

      // Update UI immediately with user message + placeholder assistant
      if (!sessionId) {
        sessionId = crypto.randomUUID();
        const newSession: ChatSession = {
          id: sessionId,
          title: userMessage.content.slice(0, 30) + (userMessage.content.length > 30 ? "..." : ""),
          messages: [userMessage, { role: "assistant", content: "" }],
          updatedAt: Date.now(),
        };
        setSessions((prev) => [newSession, ...prev]);
        setActiveSessionId(sessionId);
      } else {
        setSessions((prev) =>
          prev.map((s) =>
            s.id === sessionId
              ? { ...s, messages: [...(s.messages || []), userMessage, { role: "assistant", content: "" }] }
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
            chat_history: currentHistory.map((m) => ({ role: m.role, content: m.content })),
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

        const sid = sessionId;
        await readChatStream(response, {
          onToken: (accumulated) => {
            updateLastAssistantMessage(sid, (msg) => ({ ...msg, content: accumulated }));
          },
          onDone: (sources, rewrittenQuery) => {
            updateLastAssistantMessage(sid, (msg) => ({ ...msg, sources, rewrittenQuery }));
          },
        });
      } catch (error) {
        console.error("Lỗi Stream:", error);
        const sid = sessionId;
        updateLastAssistantMessage(sid, () => ({
          role: "assistant",
          content: UI_MESSAGES.ERROR_CONNECTION,
        }));
      } finally {
        setIsLoading(false);
      }
    },
    [input, isLoading, activeSessionId, activeSession, router, clearToken, updateLastAssistantMessage],
  );

  // Logout
  const handleLogout = useCallback(() => {
    clearToken();
    router.push("/login");
  }, [router, clearToken]);

  // Return hook
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
    isAboutOpen,
    setIsAboutOpen,
    isAccountOpen,
    setIsAccountOpen,

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
