"use client";

import { create } from "zustand";

// ==========================================
// TYPE DEFINITIONS
// ==========================================
interface ThemeState {
  isDark: boolean;
  initialize: () => void;
  toggleTheme: () => void;
}

// ==========================================
// ZUSTAND STORE
// ==========================================
export const useThemeStore = create<ThemeState>((set) => ({
  isDark: false,

  // Load saved theme from localStorage
  initialize: () => {
    const saved = localStorage.getItem("dental_theme");
    if (saved === "dark") {
      document.documentElement.classList.add("dark");
      set({ isDark: true });
    }
  },

  // Toggle dark/light mode
  toggleTheme: () => {
    set((state) => {
      const newValue = !state.isDark;
      if (newValue) {
        document.documentElement.classList.add("dark");
        localStorage.setItem("dental_theme", "dark");
      } else {
        document.documentElement.classList.remove("dark");
        localStorage.setItem("dental_theme", "light");
      }
      return { isDark: newValue };
    });
  },
}));
