"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/use-auth-store";

// Check Auth When Entering Login/Register Page
// Redirect to "/" if authenticated, otherwise open normal page.

// Auth Redirect Hook
export function useAuthRedirect() {
  const router = useRouter();
  const { initialize } = useAuthStore();
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Check Auth When Entering Login/Register Page
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
