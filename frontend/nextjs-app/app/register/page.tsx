"use client";

import { useState } from "react";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, UserPlus } from "lucide-react";
import { useRegisterForm } from "@/hooks/use-register";
import { AuthLayout } from "@/components/auth/auth-layout";
import { PasswordInput } from "@/components/auth/password-input";
import { APP_CONFIG } from "@/lib/constants";

export default function RegisterPage() {
  const [termsOpen, setTermsOpen] = useState(false);
  const [privacyOpen, setPrivacyOpen] = useState(false);

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
            Tạo tài khoản mới để sử dụng {APP_CONFIG.NAME}.
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
                placeholder="Nguyen Van A"
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
                  <button
                    type="button"
                    className="text-primary hover:underline"
                    onClick={() => setTermsOpen(true)}
                  >
                    điều khoản sử dụng
                  </button>{" "}
                  và{" "}
                  <button
                    type="button"
                    className="text-primary hover:underline"
                    onClick={() => setPrivacyOpen(true)}
                  >
                    chính sách bảo mật
                  </button>
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
                <>
                  <UserPlus className="size-4" />
                  Đăng ký
                </>
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
      <Dialog open={termsOpen} onOpenChange={setTermsOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Điều khoản sử dụng</DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[60vh] pr-4">
            <div className="space-y-4 text-sm text-muted-foreground leading-relaxed">
              <p className="font-medium text-foreground">
                Cập nhật lần cuối: {new Date().toLocaleDateString('vi-VN', { year: 'numeric', month: 'long', day: 'numeric' })}
              </p>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">1. Chấp nhận điều khoản</h3>
                <p>
                  Bằng việc truy cập và sử dụng {APP_CONFIG.NAME}, bạn đồng ý tuân thủ các điều khoản được nêu trong tài liệu này. Nếu không đồng ý, vui lòng ngừng sử dụng dịch vụ.
                </p>
              </section>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">2. Mô tả dịch vụ</h3>
                <p>
                  {APP_CONFIG.NAME} là hệ thống trợ lý AI hỗ trợ tư vấn thông tin nha khoa. Hệ thống cung cấp thông tin mang tính tham khảo, KHÔNG thay thế cho việc khám và tư vấn trực tiếp từ bác sĩ nha khoa.
                </p>
              </section>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">3. Giới hạn trách nhiệm</h3>
                <p>
                  Thông tin do AI cung cấp chỉ mang tính chất tham khảo. Chúng tôi không chịu trách nhiệm cho bất kỳ quyết định y tế nào được đưa ra dựa trên nội dung tư vấn từ hệ thống. Người dùng cần tham khảo ý kiến bác sĩ chuyên khoa trước khi thực hiện bất kỳ phương pháp điều trị nào.
                </p>
              </section>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">4. Tài khoản người dùng</h3>
                <p>
                  Bạn chịu trách nhiệm bảo mật thông tin đăng nhập của mình. Mọi hoạt động phát sinh từ tài khoản của bạn đều thuộc trách nhiệm của bạn.
                </p>
              </section>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">5. Sử dụng hợp lý</h3>
                <p>
                  Người dùng không được sử dụng hệ thống cho các mục đích bất hợp pháp, spam, hoặc gây hại cho người khác. Chúng tôi có quyền tạm ngưng hoặc chấm dứt tài khoản vi phạm.
                </p>
              </section>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">6. Thay đổi điều khoản</h3>
                <p>
                  Chúng tôi có quyền cập nhật điều khoản bất kỳ lúc nào. Việc tiếp tục sử dụng dịch vụ sau khi thay đổi đồng nghĩa với việc bạn chấp nhận điều khoản mới.
                </p>
              </section>
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      <Dialog open={privacyOpen} onOpenChange={setPrivacyOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Chính sách bảo mật</DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[60vh] pr-4">
            <div className="space-y-4 text-sm text-muted-foreground leading-relaxed">
              <p className="font-medium text-foreground">
                Cập nhật lần cuối: {new Date().toLocaleDateString('vi-VN', { year: 'numeric', month: 'long', day: 'numeric' })}
              </p>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">1. Thông tin thu thập</h3>
                <p>
                  Chúng tôi thu thập: họ tên, email, mật khẩu (đã mã hóa) khi đăng ký tài khoản, và nội dung hội thoại khi sử dụng dịch vụ tư vấn.
                </p>
              </section>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">2. Mục đích sử dụng</h3>
                <p>
                  Thông tin được sử dụng để: xác thực tài khoản, lưu lịch sử hội thoại, cải thiện chất lượng dịch vụ, và hỗ trợ kỹ thuật khi cần thiết.
                </p>
              </section>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">3. Bảo mật dữ liệu</h3>
                <p>
                  Mật khẩu được mã hóa bằng thuật toán bcrypt. Phiên đăng nhập được bảo vệ bằng JWT token. Hệ thống hỗ trợ xác thực hai yếu tố (2FA) để tăng cường bảo mật.
                </p>
              </section>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">4. Chia sẻ thông tin</h3>
                <p>
                  Chúng tôi KHÔNG bán, trao đổi hoặc chia sẻ thông tin cá nhân của bạn cho bên thứ ba, ngoại trừ trường hợp được yêu cầu bởi pháp luật.
                </p>
              </section>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">5. Quyền của người dùng</h3>
                <p>
                  Bạn có quyền: xem và chỉnh sửa thông tin cá nhân, xóa lịch sử hội thoại, xóa tài khoản và toàn bộ dữ liệu liên quan bất kỳ lúc nào.
                </p>
              </section>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">6. Lưu trữ dữ liệu</h3>
                <p>
                  Dữ liệu được lưu trữ trên máy chủ bảo mật. Nội dung hội thoại được lưu để phục vụ tính năng xem lại lịch sử. Bạn có thể xóa toàn bộ lịch sử bất kỳ lúc nào.
                </p>
              </section>

              <section>
                <h3 className="mb-1 font-semibold text-foreground">7. Liên hệ</h3>
                <p>
                  Nếu có thắc mắc về chính sách bảo mật, vui lòng liên hệ qua email <a href={`mailto:${APP_CONFIG.EMAIL}`} className="text-primary hover:underline">{APP_CONFIG.EMAIL}</a> hoặc số điện thoại <a href={`tel:${APP_CONFIG.PHONE}`} className="text-primary hover:underline">{APP_CONFIG.PHONE}</a> để được hỗ trợ.
                </p>
                <p>
                  Địa chỉ: {APP_CONFIG.ADDRESS}
                </p>
              </section>
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </AuthLayout>
  );
}
