"use client";

import { create } from "zustand";
import { APP_CONFIG } from "@/lib/constants";

// Type Definitions
export interface UserInfo {
  fullName: string;
  email: string;
}

// Kết quả đăng nhập
interface LoginResult {
  success: boolean;
  error?: string;
  requires2FA?: boolean;
  tempToken?: string;
}

// Kết quả hành động
interface ActionResult {
  success: boolean;
  error?: string;
}

// Trạng thái xác thực
interface AuthState {
  token: string | null;
  user: UserInfo | null;
  isAuthenticated: boolean;

  initialize: () => string | null;
  setToken: (token: string) => void;
  clearToken: () => void;
  setUser: (user: UserInfo) => void;
  fetchProfile: () => Promise<void>;
  login: (email: string, password: string) => Promise<LoginResult>;
  verify2FALogin: (
    tempToken: string,
    totpCode: string,
  ) => Promise<ActionResult>;
  register: (data: {
    fullName: string;
    email: string;
    password: string;
    confirmPassword: string;
  }) => Promise<ActionResult>;
  changePassword: (data: {
    currentPassword: string;
    newPassword: string;
    confirmNewPassword: string;
  }) => Promise<ActionResult>;
  updateProfile: (data: { fullName: string }) => Promise<ActionResult>;
}

const API_BASE_URL = APP_CONFIG.API_URL;

// Store Zustand
export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  // Khởi tạo store Zustand
  initialize: () => {
    const token = localStorage.getItem("access_token");
    const savedUser = localStorage.getItem("user_info");
    const user = savedUser ? JSON.parse(savedUser) : null;
    set({ token, user, isAuthenticated: !!token });
    return token;
  },

  // Set token
  setToken: (token: string) => {
    localStorage.setItem("access_token", token);
    set({ token, isAuthenticated: true });
  },

  // Xóa token và thông tin user
  clearToken: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_info");
    set({ token: null, user: null, isAuthenticated: false });
  },

  // Set thông tin user
  setUser: (user: UserInfo) => {
    localStorage.setItem("user_info", JSON.stringify(user));
    set({ user });
  },

  // Tải thông tin user
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

  // Đăng nhập
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

      // 2FA required → trả về temp_token cho bước xác thực tiếp theo
      if (data.requires_2fa) {
        return {
          success: false,
          requires2FA: true,
          tempToken: data.temp_token,
        };
      }

      // Đăng nhập bình thường (không cần xác thực 2FA)
      const user: UserInfo = {
        fullName: data.full_name,
        email: data.email,
      };
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_info", JSON.stringify(user));
      set({ token: data.access_token, user, isAuthenticated: true });

      return { success: true };
    } catch {
      return {
        success: false,
        error: "Không thể kết nối đến máy chủ Backend.",
      };
    }
  },

  // Xác thực 2FA bước 2
  verify2FALogin: async (tempToken, totpCode) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/2fa/login-verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ temp_token: tempToken, totp_code: totpCode }),
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.detail || "Xác thực thất bại" };
      }

      const user: UserInfo = {
        fullName: data.full_name,
        email: data.email,
      };
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_info", JSON.stringify(user));
      set({ token: data.access_token, user, isAuthenticated: true });

      return { success: true };
    } catch {
      return {
        success: false,
        error: "Không thể kết nối đến máy chủ Backend.",
      };
    }
  },

  // Cập nhật hồ sơ
  updateProfile: async ({ fullName }) => {
    const token = get().token || localStorage.getItem("access_token");
    if (!token) return { success: false, error: "Chưa đăng nhập" };

    try {
      const response = await fetch(`${API_BASE_URL}/auth/update-profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ full_name: fullName }),
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.detail || "Cập nhật thất bại" };
      }

      const currentUser = get().user;
      if (currentUser) {
        const updated: UserInfo = { ...currentUser, fullName };
        localStorage.setItem("user_info", JSON.stringify(updated));
        set({ user: updated });
      }

      return { success: true };
    } catch {
      return {
        success: false,
        error: "Không thể kết nối đến máy chủ Backend.",
      };
    }
  },

  // Đổi mật khẩu
  changePassword: async ({
    currentPassword,
    newPassword,
    confirmNewPassword,
  }) => {
    const token = get().token || localStorage.getItem("access_token");
    if (!token) return { success: false, error: "Chưa đăng nhập" };

    try {
      const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_new_password: confirmNewPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.detail || "Đổi mật khẩu thất bại",
        };
      }

      return { success: true };
    } catch {
      return {
        success: false,
        error: "Không thể kết nối đến máy chủ Backend.",
      };
    }
  },

  // Đăng ký
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
      return {
        success: false,
        error: "Không thể kết nối đến máy chủ Backend.",
      };
    }
  },
}));
