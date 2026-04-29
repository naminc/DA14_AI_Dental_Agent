"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/use-auth-store";
import { useAuthRedirect } from "@/hooks/use-auth-redirect";
import { useToggle } from "@/hooks/use-toggle";
import { validateEmail, validatePassword } from "@/lib/validators";

// Type Definitions
export interface LoginErrors {
  email?: string;
  password?: string;
  totp?: string;
}

// Login Form Hook
export function useLoginForm() {
  const router = useRouter();
  const { login, verify2FALogin } = useAuthStore();
  const { isCheckingAuth } = useAuthRedirect();

  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, toggleShowPassword] = useToggle();
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState<LoginErrors>({});

  // Trạng thái 2FA
  const [requires2FA, setRequires2FA] = useState(false);
  const [tempToken, setTempToken] = useState("");
  const [totpCode, setTotpCode] = useState("");

  // Kiểm tra form
  const validateForm = useCallback(() => {
    const newErrors: LoginErrors = {
      email: validateEmail(formData.email),
      password: validatePassword(formData.password),
    };

    const cleaned = Object.fromEntries(
      Object.entries(newErrors).filter(([, v]) => v !== undefined),
    ) as LoginErrors;

    setErrors(cleaned);
    return Object.keys(cleaned).length === 0;
  }, [formData]);

  // Bước 1: Email + Password
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!validateForm()) return;

      setIsLoading(true);
      const result = await login(formData.email, formData.password);

      if (result.success) {
        router.push("/");
      } else if (result.requires2FA && result.tempToken) {
        setRequires2FA(true);
        setTempToken(result.tempToken);
        setErrors({});
      } else {
        setErrors({ email: result.error });
      }
      setIsLoading(false);
    },
    [formData, validateForm, login, router],
  );

  // Bước 2: Xác thực TOTP
  const handleVerify2FA = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (totpCode.length !== 6) {
        setErrors({ totp: "Vui lòng nhập đủ 6 chữ số" });
        return;
      }

      setIsLoading(true);
      const result = await verify2FALogin(tempToken, totpCode);

      if (result.success) {
        router.push("/");
      } else {
        setErrors({ totp: result.error });
      }
      setIsLoading(false);
    },
    [totpCode, tempToken, verify2FALogin, router],
  );

  // Xử lý thay đổi mã TOTP
  const handleTotpChange = useCallback(
    (value: string) => {
      setTotpCode(value.replace(/\D/g, "").slice(0, 6));
      if (errors.totp) setErrors((prev) => ({ ...prev, totp: undefined }));
    },
    [errors.totp],
  );

  // Quay lại bước 1
  const handleBack = useCallback(() => {
    setRequires2FA(false);
    setTempToken("");
    setTotpCode("");
    setErrors({});
  }, []);

  // Xử lý thay đổi input
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

  // Trả về hook đăng nhập
  return {
    isLoading,
    isCheckingAuth,
    showPassword,
    formData,
    errors,
    handleSubmit,
    handleChange,
    toggleShowPassword,
    // Trạng thái 2FA
    requires2FA,
    totpCode,
    handleTotpChange,
    handleVerify2FA,
    handleBack,
  };
}
