"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/use-auth-store";
import { useAuthRedirect } from "@/hooks/use-auth-redirect";
import { useToggle } from "@/hooks/use-toggle";
import { validateEmail, validatePassword } from "@/lib/validators";

// Type Definitions
export interface RegisterErrors {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  terms?: string;
}

// Register Form Hook
export function useRegisterForm() {
  const router = useRouter();
  const { register } = useAuthStore();
  const { isCheckingAuth } = useAuthRedirect();

  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, toggleShowPassword] = useToggle();
  const [showConfirmPassword, toggleShowConfirmPassword] = useToggle();
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<RegisterErrors>({});

  // Kiểm tra form
  const validateForm = useCallback(() => {
    const newErrors: RegisterErrors = {};

    if (!formData.fullName.trim()) {
      newErrors.fullName = "Họ tên là bắt buộc";
    } else if (formData.fullName.trim().length < 2) {
      newErrors.fullName = "Họ tên phải có ít nhất 2 ký tự";
    }

    newErrors.email = validateEmail(formData.email);
    newErrors.password = validatePassword(formData.password);

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Vui lòng xác nhận mật khẩu";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Mật khẩu xác nhận không khớp";
    }

    if (!acceptTerms) {
      newErrors.terms = "Bạn cần đồng ý với điều khoản sử dụng";
    }

    const cleaned = Object.fromEntries(
      Object.entries(newErrors).filter(([, v]) => v !== undefined),
    ) as RegisterErrors;

    setErrors(cleaned);
    return Object.keys(cleaned).length === 0;
  }, [formData, acceptTerms]);

  // Gửi → Chuyển giao API đến authStore.register()
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

  // Xử lý thay đổi input + xóa lỗi trường
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

  // Xử lý thay đổi checkbox điều khoản
  const handleTermsChange = useCallback(
    (checked: boolean) => {
      setAcceptTerms(checked);
      if (errors.terms) {
        setErrors((prev) => ({ ...prev, terms: undefined }));
      }
    },
    [errors.terms],
  );

  // Trả về hook đăng ký
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
