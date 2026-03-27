"use client";

import { create } from "zustand";

// Type Definitions
interface ThemeState {
  isDark: boolean;
  initialize: () => void;
  toggleTheme: () => void;
}

// Zustand Store
export const useThemeStore = create<ThemeState>((set) => ({
  isDark: false,

  // Load Saved Theme from LocalStorage
  initialize: () => {
    const saved = localStorage.getItem("dental_theme");
    if (saved === "dark") {
      document.documentElement.classList.add("dark");
      set({ isDark: true });
    }
  },

  // Toggle Dark/Light Mode
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
