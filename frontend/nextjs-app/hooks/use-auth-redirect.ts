"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/use-auth-store";

// Kiểm tra xác thực khi vào trang đăng nhập/đăng ký
// Chuyển hướng đến "/" nếu đã xác thực, nếu không thì mở trang bình thường.

// Hook chuyển hướng xác thực
export function useAuthRedirect() {
  const router = useRouter();
  const { initialize } = useAuthStore();
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Kiểm tra xác thực khi vào trang đăng nhập/đăng ký
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
