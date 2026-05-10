"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/use-auth-store";


// Auth Redirect Hook
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
