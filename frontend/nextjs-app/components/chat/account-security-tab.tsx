"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { TabsContent } from "@/components/ui/tabs";
import {
  Eye,
  EyeOff,
  Check,
  Smartphone,
  KeyRound,
  ShieldCheck,
  ShieldOff,
  Loader2,
  X,
} from "lucide-react";
import { useChangePasswordForm } from "@/hooks/use-change-password";
import { use2FA } from "@/hooks/use-2fa";

// ==========================================
// PASSWORD INPUT (internal helper)
// ==========================================
function PasswordInput({
  id,
  value,
  onChange,
  placeholder,
  show,
  onToggleShow,
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  show: boolean;
  onToggleShow: () => void;
}) {
  return (
    <div className="relative">
      <Input
        id={id}
        type={show ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="pr-10"
      />
      <button
        type="button"
        onClick={onToggleShow}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
      >
        {show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
      </button>
    </div>
  );
}

// ==========================================
// SECURITY TAB COMPONENT
// ==========================================
export function AccountSecurityTab() {
  const {
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
  } = useChangePasswordForm();

  const twoFA = use2FA();

  return (
    <TabsContent
      value="security"
      className="mt-0 px-6 pb-6 pt-4 space-y-6 data-[state=inactive]:hidden"
    >
      {/* ---- Change Password Section ---- */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <div className="flex size-7 items-center justify-center rounded-md bg-primary/10">
            <KeyRound className="size-3.5 text-primary" />
          </div>
          <h3 className="text-sm font-semibold">Đổi mật khẩu</h3>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3 rounded-xl border bg-muted/20 p-4">
          <div className="space-y-1.5">
            <Label
              htmlFor="current-password"
              className="text-xs font-medium text-muted-foreground"
            >
              Mật khẩu hiện tại
            </Label>
            <PasswordInput
              id="current-password"
              value={formData.currentPassword}
              onChange={(v) => handleChange("currentPassword", v)}
              placeholder="Nhập mật khẩu hiện tại"
              show={showCurrentPassword}
              onToggleShow={toggleShowCurrentPassword}
            />
            {errors.currentPassword && (
              <p className="text-xs text-destructive">{errors.currentPassword}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label
              htmlFor="new-password"
              className="text-xs font-medium text-muted-foreground"
            >
              Mật khẩu mới
            </Label>
            <PasswordInput
              id="new-password"
              value={formData.newPassword}
              onChange={(v) => handleChange("newPassword", v)}
              placeholder="Tối thiểu 6 ký tự"
              show={showNewPassword}
              onToggleShow={toggleShowNewPassword}
            />
            {errors.newPassword && (
              <p className="text-xs text-destructive">{errors.newPassword}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label
              htmlFor="confirm-new-password"
              className="text-xs font-medium text-muted-foreground"
            >
              Xác nhận mật khẩu mới
            </Label>
            <PasswordInput
              id="confirm-new-password"
              value={formData.confirmNewPassword}
              onChange={(v) => handleChange("confirmNewPassword", v)}
              placeholder="Nhập lại mật khẩu mới"
              show={showConfirmPassword}
              onToggleShow={toggleShowConfirmPassword}
            />
            {errors.confirmNewPassword && (
              <p className="text-xs text-destructive">{errors.confirmNewPassword}</p>
            )}
          </div>

          {errors.general && (
            <p className="text-xs text-destructive text-center">{errors.general}</p>
          )}

          <Button
            type="submit"
            disabled={!isFormValid || isLoading}
            className="w-full h-9 mt-1"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Đang cập nhật...
              </>
            ) : isSuccess ? (
              <>
                <Check className="mr-2 size-4" />
                Đã cập nhật mật khẩu
              </>
            ) : (
              "Cập nhật mật khẩu"
            )}
          </Button>
        </form>
      </div>

      <Separator />

      {/* ---- 2FA Section ---- */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <div className="flex size-7 items-center justify-center rounded-md bg-primary/10">
            <Smartphone className="size-3.5 text-primary" />
          </div>
          <h3 className="text-sm font-semibold">
            Xác thực hai yếu tố (2FA)
          </h3>
        </div>

        {/* Toggle card */}
        <div className="flex items-center justify-between rounded-xl border p-4">
          <div className="space-y-0.5 pr-4">
            <p className="text-sm font-medium">
              {twoFA.isEnabled ? "2FA đang bật" : "Bật xác thực 2FA"}
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Bảo vệ tài khoản bằng mã từ ứng dụng Authenticator
            </p>
          </div>
          <Switch
            id="2fa-toggle"
            checked={twoFA.isEnabled || twoFA.showSetup}
            onCheckedChange={twoFA.handleToggle}
            disabled={twoFA.isLoading}
          />
        </div>

        {/* Error message */}
        {twoFA.error && (
          <p className="text-xs text-destructive text-center">{twoFA.error}</p>
        )}

        {/* ---- 2FA Setup Flow ---- */}
        {twoFA.showSetup && !twoFA.isEnabled && twoFA.setupData && (
          <div className="space-y-4 rounded-xl border border-primary/20 bg-primary/[0.03] p-5 animate-in fade-in-0 slide-in-from-top-1 duration-200">
            <div className="text-center space-y-1">
              <p className="text-sm font-semibold">Thiết lập 2FA</p>
              <p className="text-xs text-muted-foreground">
                Quét mã QR bằng Google Authenticator hoặc Authy
              </p>
            </div>

            {/* QR Code (SVG base64 từ server) */}
            <div className="mx-auto w-40 h-40 rounded-xl border bg-background flex items-center justify-center shadow-sm p-2">
              <img
                src={`data:image/svg+xml;base64,${twoFA.setupData.qr_code}`}
                alt="QR Code"
                className="w-full h-full"
              />
            </div>

            {/* Manual secret */}
            <div className="text-center">
              <p className="text-xs text-muted-foreground mb-1.5">
                Hoặc nhập mã thủ công:
              </p>
              <code className="text-xs font-mono bg-muted px-3 py-1.5 rounded-lg select-all tracking-wider">
                {twoFA.setupData.secret}
              </code>
            </div>

            {/* Verification input */}
            <div className="space-y-2">
              <Label htmlFor="2fa-code" className="text-xs">
                Mã xác thực 6 chữ số
              </Label>
              <Input
                id="2fa-code"
                value={twoFA.verificationCode}
                onChange={(e) =>
                  twoFA.setVerificationCode(
                    e.target.value.replace(/\D/g, "").slice(0, 6),
                  )
                }
                placeholder="000000"
                className="text-center tracking-[0.4em] font-mono text-base h-11"
                maxLength={6}
              />
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={twoFA.handleCancelSetup}
                className="flex-1 h-10"
              >
                <X className="mr-2 size-4" />
                Hủy
              </Button>
              <Button
                onClick={twoFA.handleVerify}
                disabled={twoFA.verificationCode.length !== 6 || twoFA.isVerifying}
                className="flex-1 h-10"
              >
                {twoFA.isVerifying ? (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                ) : (
                  <ShieldCheck className="mr-2 size-4" />
                )}
                Xác nhận bật 2FA
              </Button>
            </div>
          </div>
        )}

        {/* ---- Disable 2FA Flow ---- */}
        {twoFA.showDisable && twoFA.isEnabled && (
          <div className="space-y-4 rounded-xl border border-destructive/20 bg-destructive/[0.03] p-5 animate-in fade-in-0 slide-in-from-top-1 duration-200">
            <div className="text-center space-y-1">
              <p className="text-sm font-semibold text-destructive">Tắt 2FA</p>
              <p className="text-xs text-muted-foreground">
                Nhập mã từ ứng dụng Authenticator để xác nhận tắt
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="2fa-disable-code" className="text-xs">
                Mã xác thực 6 chữ số
              </Label>
              <Input
                id="2fa-disable-code"
                value={twoFA.disableCode}
                onChange={(e) =>
                  twoFA.setDisableCode(
                    e.target.value.replace(/\D/g, "").slice(0, 6),
                  )
                }
                placeholder="000000"
                className="text-center tracking-[0.4em] font-mono text-base h-11"
                maxLength={6}
              />
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={twoFA.handleCancelDisable}
                className="flex-1 h-10"
              >
                <X className="mr-2 size-4" />
                Hủy
              </Button>
              <Button
                variant="destructive"
                onClick={twoFA.handleDisable}
                disabled={twoFA.disableCode.length !== 6 || twoFA.isVerifying}
                className="flex-1 h-10"
              >
                {twoFA.isVerifying ? (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                ) : (
                  <ShieldOff className="mr-2 size-4" />
                )}
                Xác nhận tắt 2FA
              </Button>
            </div>
          </div>
        )}

        {/* ---- 2FA Enabled Status ---- */}
        {twoFA.isEnabled && !twoFA.showDisable && (
          <div className="flex items-center gap-3 rounded-xl border border-emerald-200 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/10 p-4 animate-in fade-in-0 duration-200">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-500/20">
              <ShieldCheck className="size-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div className="space-y-0.5">
              <p className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
                2FA đã được kích hoạt
              </p>
              <p className="text-xs text-emerald-600/70 dark:text-emerald-400/70">
                Tài khoản đang được bảo vệ bằng xác thực hai yếu tố
              </p>
            </div>
          </div>
        )}
      </div>
    </TabsContent>
  );
}
