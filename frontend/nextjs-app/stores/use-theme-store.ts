"use client";

import { create } from "zustand";

// Theme State
interface ThemeState {
  isDark: boolean;
  initialize: () => void;
  toggleTheme: () => void;
}

// Theme Store
export const useThemeStore = create<ThemeState>((set) => ({
  isDark: false,

  // Load Saved Theme
  initialize: () => {
    const saved = localStorage.getItem("dental_theme");
    if (saved === "dark") {
      document.documentElement.classList.add("dark");
      set({ isDark: true });
    }
  },

  // Toggle Theme
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
