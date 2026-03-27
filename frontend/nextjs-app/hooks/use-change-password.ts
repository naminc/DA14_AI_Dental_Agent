"use client";

import { useState, useCallback } from "react";
import { useAuthStore } from "@/stores/use-auth-store";
import { useToggle } from "@/hooks/use-toggle";
import { validatePassword } from "@/lib/validators";

// Type Definitions
export interface ChangePasswordErrors {
  currentPassword?: string;
  newPassword?: string;
  confirmNewPassword?: string;
  general?: string;
}

// Change Password Form Hook
export function useChangePasswordForm() {
  const { changePassword } = useAuthStore();

  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [showCurrentPassword, toggleShowCurrentPassword] = useToggle();
  const [showNewPassword, toggleShowNewPassword] = useToggle();
  const [showConfirmPassword, toggleShowConfirmPassword] = useToggle();
  const [formData, setFormData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmNewPassword: "",
  });
  const [errors, setErrors] = useState<ChangePasswordErrors>({});

  // Validate Form
  const validateForm = useCallback(() => {
    const newErrors: ChangePasswordErrors = {};

    if (!formData.currentPassword) {
      newErrors.currentPassword = "Vui lòng nhập mật khẩu hiện tại";
    }

    newErrors.newPassword = validatePassword(formData.newPassword, "Mật khẩu mới");

    if (!formData.confirmNewPassword) {
      newErrors.confirmNewPassword = "Vui lòng xác nhận mật khẩu mới";
    } else if (formData.newPassword !== formData.confirmNewPassword) {
      newErrors.confirmNewPassword = "Mật khẩu xác nhận không khớp";
    }

    const cleaned = Object.fromEntries(
      Object.entries(newErrors).filter(([, v]) => v !== undefined),
    ) as ChangePasswordErrors;

    setErrors(cleaned);
    return Object.keys(cleaned).length === 0;
  }, [formData]);

  // Submit → Delegate API Call to authStore.changePassword()
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!validateForm()) return;

      setIsLoading(true);
      const result = await changePassword(formData);

      if (result.success) {
        setIsSuccess(true);
        setFormData({ currentPassword: "", newPassword: "", confirmNewPassword: "" });
        setTimeout(() => setIsSuccess(false), 3000);
      } else {
        setErrors({ general: result.error });
      }
      setIsLoading(false);
    },
    [formData, validateForm, changePassword],
  );

  // Handle Input Change + Clear Field Error
  const handleChange = useCallback(
    (field: keyof typeof formData, value: string) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
      if (errors[field as keyof ChangePasswordErrors]) {
        setErrors((prev) => ({ ...prev, [field]: undefined, general: undefined }));
      }
    },
    [errors],
  );

  // Check if Form is Valid
  const isFormValid =
    formData.currentPassword.length > 0 &&
    formData.newPassword.length >= 6 &&
    formData.newPassword === formData.confirmNewPassword;

  // Return Change Password Form Hook
  return {
    isLoading,
    isSuccess,
    showCurrentPassword,
    showNewPassword,
    showConfirmPassword,
    formData,
    errors,
    isFormValid,
    handleSubmit,
    handleChange,
    toggleShowCurrentPassword,
    toggleShowNewPassword,
    toggleShowConfirmPassword,
  };
}
