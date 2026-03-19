"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Loader2, ShieldCheck } from "lucide-react";
import { useLoginForm } from "@/hooks/use-login";
import { AuthLayout } from "@/components/auth/auth-layout";
import { PasswordInput } from "@/components/auth/password-input";

export default function LoginPage() {
  const {
    isLoading,
    isCheckingAuth,
    showPassword,
    formData,
    errors,
    handleSubmit,
    handleChange,
    toggleShowPassword,
    requires2FA,
    totpCode,
    handleTotpChange,
    handleVerify2FA,
    handleBack,
  } = useLoginForm();

  return (
    <AuthLayout isCheckingAuth={isCheckingAuth}>
      {requires2FA ? (
        /* ---- Step 2: TOTP Verification ---- */
        <Card className="w-full max-w-md gap-4 bg-white/95 dark:bg-gray-900/95 shadow-lg border-0">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
              <ShieldCheck className="h-6 w-6 text-primary" />
            </div>
            <CardTitle className="text-2xl font-bold">Xác thực 2FA</CardTitle>
            <CardDescription>
              Nhập mã 6 chữ số từ ứng dụng Authenticator
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleVerify2FA}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="totp-code">Mã xác thực</Label>
                <Input
                  id="totp-code"
                  value={totpCode}
                  onChange={(e) => handleTotpChange(e.target.value)}
                  placeholder="000000"
                  className="text-center tracking-[0.4em] font-mono text-lg h-12"
                  maxLength={6}
                  autoFocus
                  disabled={isLoading}
                />
                {errors.totp && (
                  <p className="text-sm text-destructive text-center">
                    {errors.totp}
                  </p>
                )}
              </div>
            </CardContent>
            <CardFooter className="flex flex-col gap-3 pt-4">
              <Button type="submit" className="w-full" disabled={isLoading || totpCode.length !== 6}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Đang xác thực...
                  </>
                ) : (
                  "Xác nhận"
                )}
              </Button>
              <Button
                type="button"
                variant="ghost"
                className="w-full"
                onClick={handleBack}
                disabled={isLoading}
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Quay lại đăng nhập
              </Button>
            </CardFooter>
          </form>
        </Card>
      ) : (
        /* ---- Step 1: Email + Password ---- */
        <Card className="w-full max-w-md gap-4 bg-white/95 dark:bg-gray-900/95 shadow-lg border-0">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-6 w-6 text-primary"
              >
                <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12A10 10 0 0 1 12 2" />
                <path d="M8 14s1.5 2 4 2 4-2 4-2" />
                <path d="M9 9h.01" />
                <path d="M15 9h.01" />
              </svg>
            </div>
            <CardTitle className="text-2xl font-bold">Đăng nhập</CardTitle>
            <CardDescription>
              Chào mừng bạn trở lại! Đăng nhập để tiếp tục.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="name@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  disabled={isLoading}
                  aria-invalid={!!errors.email}
                />
                {errors.email && (
                  <p className="text-sm text-destructive">{errors.email}</p>
                )}
              </div>
              <PasswordInput
                id="password"
                name="password"
                label="Mật khẩu"
                value={formData.password}
                showPassword={showPassword}
                error={errors.password}
                disabled={isLoading}
                onToggle={toggleShowPassword}
                onChange={handleChange}
              />
            </CardContent>
            <CardFooter className="flex flex-col gap-3 pt-4">
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Đang đăng nhập...
                  </>
                ) : (
                  "Đăng nhập"
                )}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                Chưa có tài khoản?{" "}
                <Link href="/register" className="text-primary hover:underline">
                  Đăng ký ngay
                </Link>
              </p>
            </CardFooter>
          </form>
        </Card>
      )}
    </AuthLayout>
  );
}
