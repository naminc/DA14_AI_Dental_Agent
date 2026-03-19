"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/use-auth-store";

// ==========================================
// CUSTOM HOOK — Kiểm tra auth khi vào trang login/register
// Redirect về "/" nếu đã đăng nhập, ngược lại mở trang bình thường.
// ==========================================
export function useAuthRedirect() {
  const router = useRouter();
  const { initialize } = useAuthStore();
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    const token = initialize();
    if (token) {
      router.replace("/");
    } else {
      setIsCheckingAuth(false);
    }
  }, [router, initialize]);

  return { isCheckingAuth };
}
