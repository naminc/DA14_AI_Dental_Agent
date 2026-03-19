"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuthStore } from "@/stores/use-auth-store";
import { APP_CONFIG } from "@/lib/constants";

const API_URL = APP_CONFIG.API_URL;

interface SetupData {
  secret: string;
  qr_code: string;
}

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

  const headers = useCallback(
    () => ({
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    }),
    [token],
  );

  // Fetch trạng thái 2FA khi mount
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
        /* ignore */
      } finally {
        setIsLoading(false);
      }
    })();
  }, [token]);

  // Toggle switch
  const handleToggle = useCallback(
    async (checked: boolean) => {
      setError("");

      if (checked && !isEnabled) {
        // Bắt đầu setup flow
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

  // Xác nhận mã TOTP để BẬT 2FA
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

  // Xác nhận mã TOTP để TẮT 2FA
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

  const handleCancelSetup = useCallback(() => {
    setShowSetup(false);
    setSetupData(null);
    setVerificationCode("");
    setError("");
  }, []);

  const handleCancelDisable = useCallback(() => {
    setShowDisable(false);
    setDisableCode("");
    setError("");
  }, []);

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
