"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/use-auth-store";

// ==========================================
// TYPE DEFINITIONS
// ==========================================
export interface RegisterErrors {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  terms?: string;
}

// ==========================================
// CUSTOM HOOK — Form logic only
// ==========================================
export function useRegisterForm() {
  const router = useRouter();
  const { initialize, register } = useAuthStore();

  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<RegisterErrors>({});

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
    const newErrors: RegisterErrors = {};

    if (!formData.fullName.trim()) {
      newErrors.fullName = "Họ tên là bắt buộc";
    } else if (formData.fullName.trim().length < 2) {
      newErrors.fullName = "Họ tên phải có ít nhất 2 ký tự";
    }

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

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Vui lòng xác nhận mật khẩu";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Mật khẩu xác nhận không khớp";
    }

    if (!acceptTerms) {
      newErrors.terms = "Bạn cần đồng ý với điều khoản sử dụng";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData, acceptTerms]);

  // Submit → delegates API call to authStore.register()
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!validateForm()) return;

      setIsLoading(true);
      const result = await register({
        fullName: formData.fullName,
        email: formData.email,
        password: formData.password,
        confirmPassword: formData.confirmPassword,
      });

      if (result.success) {
        alert("Đăng ký thành công! Mời bạn đăng nhập.");
        router.push("/login");
      } else {
        setErrors((prev) => ({ ...prev, email: result.error }));
      }
      setIsLoading(false);
    },
    [formData, validateForm, register, router],
  );

  // Handle input change
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const { name, value } = e.target;
      setFormData((prev) => ({ ...prev, [name]: value }));
      if (errors[name as keyof RegisterErrors]) {
        setErrors((prev) => ({ ...prev, [name]: undefined }));
      }
    },
    [errors],
  );

  // Handle terms checkbox
  const handleTermsChange = useCallback(
    (checked: boolean) => {
      setAcceptTerms(checked);
      if (errors.terms) {
        setErrors((prev) => ({ ...prev, terms: undefined }));
      }
    },
    [errors.terms],
  );

  const toggleShowPassword = useCallback(() => {
    setShowPassword((prev) => !prev);
  }, []);

  const toggleShowConfirmPassword = useCallback(() => {
    setShowConfirmPassword((prev) => !prev);
  }, []);

  return {
    isLoading,
    isCheckingAuth,
    showPassword,
    showConfirmPassword,
    acceptTerms,
    formData,
    errors,
    handleSubmit,
    handleChange,
    handleTermsChange,
    toggleShowPassword,
    toggleShowConfirmPassword,
  };
}
