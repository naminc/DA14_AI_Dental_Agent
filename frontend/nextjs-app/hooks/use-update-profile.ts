"use client";

import { useState, useCallback } from "react";
import { useAuthStore } from "@/stores/use-auth-store";
import { validateFullName } from "@/lib/validators";
import type { UserInfo } from "@/stores/use-auth-store";

// ==========================================
// TYPE DEFINITIONS
// ==========================================
export interface UpdateProfileErrors {
  fullName?: string;
  general?: string;
}

// ==========================================
// CUSTOM HOOK — Form logic only
// ==========================================
export function useUpdateProfileForm(user: UserInfo | null) {
  const { updateProfile } = useAuthStore();

  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [fullName, setFullName] = useState(user?.fullName || "");
  const [errors, setErrors] = useState<UpdateProfileErrors>({});

  // Validate
  const validateForm = useCallback(() => {
    const fullNameError = validateFullName(fullName);
    const newErrors: UpdateProfileErrors = {};
    if (fullNameError) newErrors.fullName = fullNameError;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [fullName]);

  // Submit → delegates API call to authStore.updateProfile()
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

  // Handle input change + clear error
  const handleChange = useCallback((value: string) => {
    setFullName(value);
    setErrors({});
  }, []);

  const isFormValid = fullName.trim().length >= 2;
  const isUnchanged = fullName.trim() === (user?.fullName || "").trim();

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
