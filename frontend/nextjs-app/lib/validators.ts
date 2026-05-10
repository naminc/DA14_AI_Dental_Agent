import { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 6;

// Validate email
export function validateEmail(email: string): string | undefined {
  if (!email) return "Email là bắt buộc";
  if (!EMAIL_REGEX.test(email)) return "Email không hợp lệ";
  return undefined;
}

// Validate full name
export function validateFullName(fullName: string): string | undefined {
  if (!fullName.trim()) return "Họ và tên là bắt buộc";
  if (fullName.trim().length < 2) return "Họ và tên phải có ít nhất 2 ký tự";
  return undefined;
}

// Validate password
export function validatePassword(password: string, fieldLabel = "Mật khẩu"): string | undefined {
  if (!password) return `${fieldLabel} là bắt buộc`;
  if (password.length < MIN_PASSWORD_LENGTH)
    return `${fieldLabel} phải có ít nhất ${MIN_PASSWORD_LENGTH} ký tự`;
  return undefined;
}

// Validate token
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

// Validate chat input
export function validateChatInput(input: string, isLoading: boolean): boolean {
  return input.trim().length > 0 && !isLoading;
}

// Show confirmation dialog
export function confirmAction(message: string): boolean {
  return window.confirm(message);
}
