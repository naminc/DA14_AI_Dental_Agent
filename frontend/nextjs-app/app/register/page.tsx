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
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2 } from "lucide-react";
import { useRegisterForm } from "@/hooks/use-register";
import { AuthLayout } from "@/components/auth/auth-layout";
import { PasswordInput } from "@/components/auth/password-input";

export default function RegisterPage() {
  const {
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
  } = useRegisterForm();

  return (
    <AuthLayout isCheckingAuth={isCheckingAuth}>
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
          <CardTitle className="text-2xl font-bold">Đăng ký</CardTitle>
          <CardDescription>
            Tạo tài khoản mới để sử dụng Dental AI
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fullName">Họ và tên</Label>
              <Input
                id="fullName"
                name="fullName"
                type="text"
                placeholder="Nguyễn Văn A"
                value={formData.fullName}
                onChange={handleChange}
                disabled={isLoading}
                aria-invalid={!!errors.fullName}
              />
              {errors.fullName && (
                <p className="text-sm text-destructive">{errors.fullName}</p>
              )}
            </div>
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
            <PasswordInput
              id="confirmPassword"
              name="confirmPassword"
              label="Xác nhận mật khẩu"
              value={formData.confirmPassword}
              showPassword={showConfirmPassword}
              error={errors.confirmPassword}
              disabled={isLoading}
              onToggle={toggleShowConfirmPassword}
              onChange={handleChange}
            />
            <div className="flex items-start space-x-2">
              <Checkbox
                id="terms"
                checked={acceptTerms}
                onCheckedChange={(checked) =>
                  handleTermsChange(checked as boolean)
                }
                disabled={isLoading}
              />
              <div className="grid gap-1.5 leading-none">
                <label
                  htmlFor="terms"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  Tôi đồng ý với{" "}
                  <Link href="/terms" className="text-primary hover:underline">
                    điều khoản sử dụng
                  </Link>{" "}
                  và{" "}
                  <Link
                    href="/privacy"
                    className="text-primary hover:underline"
                  >
                    chính sách bảo mật
                  </Link>
                </label>
                {errors.terms && (
                  <p className="text-xs text-destructive">{errors.terms}</p>
                )}
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-3 pt-4">
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Đang đăng ký...
                </>
              ) : (
                "Đăng ký"
              )}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Đã có tài khoản?{" "}
              <Link href="/login" className="text-primary hover:underline">
                Đăng nhập
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </AuthLayout>
  );
}
