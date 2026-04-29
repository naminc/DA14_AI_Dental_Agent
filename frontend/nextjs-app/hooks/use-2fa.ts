"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuthStore } from "@/stores/use-auth-store";
import { APP_CONFIG } from "@/lib/constants";

const API_URL = APP_CONFIG.API_URL;

// Setup Data Type
interface SetupData {
  secret: string;
  qr_code: string;
}

// 2FA Hook
export function use2FA() {
  const token =
    useAuthStore((s) => s.token) ??
    (typeof window !== "undefined" ? localStorage.getItem("access_token") : null);

  const [isEnabled, setIsEnabled] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isVerifying, setIsVerifying] = useState(false);
  const [showSetup, setShowSetup] = useState(false);
  const [showDisable, setShowDisable] = useState(false);
  const [setupData, setSetupData] = useState<SetupData | null>(null);
  const [verificationCode, setVerificationCode] = useState("");
  const [disableCode, setDisableCode] = useState("");
  const [error, setError] = useState("");

  // Headers
  const headers = useCallback(
    () => ({
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    }),
    [token],
  );

  // Fetch 2FA Status When Mount
  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    (async () => {
      try {
        const res = await fetch(`${API_URL}/auth/2fa/status`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setIsEnabled(data.is_enabled);
        }
      } catch {
        // Bỏ qua lỗi
      } finally {
        setIsLoading(false);
      }
    })();
  }, [token]);

  // Chuyển đổi trạng thái
  const handleToggle = useCallback(
    async (checked: boolean) => {
      setError("");

      if (checked && !isEnabled) {
        // Bắt đầu quy trình thiết lập 2FA
        setIsLoading(true);
        try {
          const res = await fetch(`${API_URL}/auth/2fa/setup`, {
            method: "POST",
            headers: headers(),
          });

          if (res.ok) {
            const data: SetupData = await res.json();
            setSetupData(data);
            setShowSetup(true);
          } else {
            const err = await res.json();
            setError(err.detail || "Không thể thiết lập 2FA");
          }
        } catch {
          setError("Không thể kết nối server");
        } finally {
          setIsLoading(false);
        }
      } else if (!checked && isEnabled) {
        setShowDisable(true);
      }
    },
    [isEnabled, headers],
  );

  // Xác nhận mã TOTP để bật 2FA
  const handleVerify = useCallback(async () => {
    setIsVerifying(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/auth/2fa/verify`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ totp_code: verificationCode }),
      });

      if (res.ok) {
        setIsEnabled(true);
        setShowSetup(false);
        setSetupData(null);
        setVerificationCode("");
      } else {
        const err = await res.json();
        setError(err.detail || "Mã xác thực không đúng");
      }
    } catch {
      setError("Không thể kết nối server");
    } finally {
      setIsVerifying(false);
    }
  }, [verificationCode, headers]);

  // Xác nhận mã TOTP để tắt 2FA
  const handleDisable = useCallback(async () => {
    setIsVerifying(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/auth/2fa/disable`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ totp_code: disableCode }),
      });

      if (res.ok) {
        setIsEnabled(false);
        setShowDisable(false);
        setDisableCode("");
      } else {
        const err = await res.json();
        setError(err.detail || "Mã xác thực không đúng");
      }
    } catch {
      setError("Không thể kết nối server");
    } finally {
      setIsVerifying(false);
    }
  }, [disableCode, headers]);

  // Hủy thiết lập 2FA
  const handleCancelSetup = useCallback(() => {
    setShowSetup(false);
    setSetupData(null);
    setVerificationCode("");
    setError("");
  }, []);

  // Hủy tắt 2FA
  const handleCancelDisable = useCallback(() => {
    setShowDisable(false);
    setDisableCode("");
    setError("");
  }, []);

  // Trả về hook 2FA
  return {
    isEnabled,
    isLoading,
    isVerifying,
    showSetup,
    showDisable,
    setupData,
    verificationCode,
    disableCode,
    error,
    setVerificationCode,
    setDisableCode,
    handleToggle,
    handleVerify,
    handleDisable,
    handleCancelSetup,
    handleCancelDisable,
  };
}
