"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/use-auth-store";

// ==========================================
// TYPE DEFINITIONS
// ==========================================
export interface LoginErrors {
  email?: string;
  password?: string;
}

// ==========================================
// CUSTOM HOOK — Form logic only
// ==========================================
export function useLoginForm() {
  const router = useRouter();
  const { initialize, login } = useAuthStore();

  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState<LoginErrors>({});

  // Check if already authenticated → redirect
  useEffect(() => {
    const token = initialize();
    if (token) {
      router.replace("/");
    } else {
      setIsCheckingAuth(false);
    }
  }, [router, initialize]);

  // Validate
  const validateForm = useCallback(() => {
    const newErrors: LoginErrors = {};

    if (!formData.email) {
      newErrors.email = "Email là bắt buộc";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Email không hợp lệ";
    }

    if (!formData.password) {
      newErrors.password = "Mật khẩu là bắt buộc";
    } else if (formData.password.length < 6) {
      newErrors.password = "Mật khẩu phải có ít nhất 6 ký tự";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  // Submit → delegates API call to authStore.login()
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!validateForm()) return;

      setIsLoading(true);
      const result = await login(formData.email, formData.password);

      if (result.success) {
        router.push("/");
      } else {
        setErrors({ email: result.error });
      }
      setIsLoading(false);
    },
    [formData, validateForm, login, router],
  );

  // Handle input change
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const { name, value } = e.target;
      setFormData((prev) => ({ ...prev, [name]: value }));
      if (errors[name as keyof LoginErrors]) {
        setErrors((prev) => ({ ...prev, [name]: undefined }));
      }
    },
    [errors],
  );

  // Toggle password visibility
  const toggleShowPassword = useCallback(() => {
    setShowPassword((prev) => !prev);
  }, []);

  return {
    isLoading,
    isCheckingAuth,
    showPassword,
    formData,
    errors,
    handleSubmit,
    handleChange,
    toggleShowPassword,
  };
}
