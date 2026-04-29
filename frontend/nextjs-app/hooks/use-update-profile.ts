"use client";

import { useState, useCallback } from "react";
import { useAuthStore } from "@/stores/use-auth-store";
import { validateFullName } from "@/lib/validators";
import type { UserInfo } from "@/stores/use-auth-store";

// Type Definitions
export interface UpdateProfileErrors {
  fullName?: string;
  general?: string;
}

// Update Profile Form Hook
export function useUpdateProfileForm(user: UserInfo | null) {
  const { updateProfile } = useAuthStore();

  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [fullName, setFullName] = useState(user?.fullName || "");
  const [errors, setErrors] = useState<UpdateProfileErrors>({});

  // Kiểm tra form
  const validateForm = useCallback(() => {
    const fullNameError = validateFullName(fullName);
    const newErrors: UpdateProfileErrors = {};
    if (fullNameError) newErrors.fullName = fullNameError;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [fullName]);

  // Gửi → Chuyển giao API đến authStore.updateProfile()
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!validateForm()) return;

      setIsLoading(true);
      const result = await updateProfile({ fullName: fullName.trim() });

      if (result.success) {
        setIsSuccess(true);
        setTimeout(() => setIsSuccess(false), 3000);
      } else {
        setErrors({ general: result.error });
      }
      setIsLoading(false);
    },
    [fullName, validateForm, updateProfile],
  );

  // Xử lý thay đổi input + xóa lỗi trường
  const handleChange = useCallback((value: string) => {
    setFullName(value);
    setErrors({});
  }, []);

  // Kiểm tra form có hợp lệ không
  const isFormValid = fullName.trim().length >= 2;
  const isUnchanged = fullName.trim() === (user?.fullName || "").trim();

  // Trả về hook cập nhật hồ sơ
  return {
    isLoading,
    isSuccess,
    fullName,
    errors,
    isFormValid,
    isUnchanged,
    handleSubmit,
    handleChange,
  };
}
