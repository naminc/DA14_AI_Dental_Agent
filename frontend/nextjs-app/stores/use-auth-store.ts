"use client";

import { create } from "zustand";
import { APP_CONFIG } from "@/lib/constants";

// ==========================================
// TYPE DEFINITIONS
// ==========================================
export interface UserInfo {
  fullName: string;
  email: string;
}

interface AuthState {
  token: string | null;
  user: UserInfo | null;
  isAuthenticated: boolean;

  // Actions
  initialize: () => string | null;
  setToken: (token: string) => void;
  clearToken: () => void;
  setUser: (user: UserInfo) => void;
  fetchProfile: () => Promise<void>;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (data: {
    fullName: string;
    email: string;
    password: string;
    confirmPassword: string;
  }) => Promise<{ success: boolean; error?: string }>;
}

const API_BASE_URL = APP_CONFIG.API_URL;

// ==========================================
// ZUSTAND STORE
// ==========================================
export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  // Read token from localStorage (client-side only)
  initialize: () => {
    const token = localStorage.getItem("access_token");
    const savedUser = localStorage.getItem("user_info");
    const user = savedUser ? JSON.parse(savedUser) : null;
    set({ token, user, isAuthenticated: !!token });
    return token;
  },

  // Save token
  setToken: (token: string) => {
    localStorage.setItem("access_token", token);
    set({ token, isAuthenticated: true });
  },

  // Remove token (logout)
  clearToken: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_info");
    set({ token: null, user: null, isAuthenticated: false });
  },

  // Save user info
  setUser: (user: UserInfo) => {
    localStorage.setItem("user_info", JSON.stringify(user));
    set({ user });
  },

  // Fetch user profile from /auth/me
  fetchProfile: async () => {
    const token = get().token || localStorage.getItem("access_token");
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        const user: UserInfo = {
          fullName: data.full_name,
          email: data.email,
        };
        localStorage.setItem("user_info", JSON.stringify(user));
        set({ user });
      }
    } catch {
      console.error("Không thể lấy thông tin user");
    }
  },

  // Login API call
  login: async (email, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.detail || "Đăng nhập thất bại" };
      }

      // Save token + user info
      const user: UserInfo = {
        fullName: data.full_name,
        email: data.email,
      };
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_info", JSON.stringify(user));
      set({ token: data.access_token, user, isAuthenticated: true });

      return { success: true };
    } catch {
      return { success: false, error: "Không thể kết nối đến máy chủ Backend." };
    }
  },

  // Register API call
  register: async ({ fullName, email, password, confirmPassword }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          confirm_password: confirmPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.detail || "Đăng ký thất bại" };
      }

      return { success: true };
    } catch {
      return { success: false, error: "Không thể kết nối đến máy chủ Backend." };
    }
  },
}));
