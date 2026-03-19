import { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 6;

/**
 * Kiểm tra email hợp lệ. Trả về thông báo lỗi hoặc undefined nếu hợp lệ.
 */
export function validateEmail(email: string): string | undefined {
  if (!email) return "Email là bắt buộc";
  if (!EMAIL_REGEX.test(email)) return "Email không hợp lệ";
  return undefined;
}

/**
 * Kiểm tra họ tên hợp lệ. Trả về thông báo lỗi hoặc undefined nếu hợp lệ.
 */
export function validateFullName(fullName: string): string | undefined {
  if (!fullName.trim()) return "Họ và tên là bắt buộc";
  if (fullName.trim().length < 2) return "Họ và tên phải có ít nhất 2 ký tự";
  return undefined;
}

/**
 * Kiểm tra mật khẩu hợp lệ. Trả về thông báo lỗi hoặc undefined nếu hợp lệ.
 */
export function validatePassword(password: string, fieldLabel = "Mật khẩu"): string | undefined {
  if (!password) return `${fieldLabel} là bắt buộc`;
  if (password.length < MIN_PASSWORD_LENGTH)
    return `${fieldLabel} phải có ít nhất ${MIN_PASSWORD_LENGTH} ký tự`;
  return undefined;
}

/**
 * Kiểm tra token hợp lệ. Nếu không có, redirect về /login và return null.
 */
export function validateToken(
  router: AppRouterInstance,
  clearToken: () => void,
): string | null {
  const token = localStorage.getItem("access_token");
  if (!token) {
    clearToken();
    router.push("/login");
    return null;
  }
  return token;
}

/**
 * Kiểm tra xem input chat có hợp lệ không.
 */
export function validateChatInput(input: string, isLoading: boolean): boolean {
  return input.trim().length > 0 && !isLoading;
}

/**
 * Hiện hộp thoại xác nhận. Return true nếu người dùng đồng ý.
 */
export function confirmAction(message: string): boolean {
  return window.confirm(message);
}
