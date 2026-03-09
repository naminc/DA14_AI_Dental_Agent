import { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

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
