import { Loader2 } from "lucide-react";

interface AuthLayoutProps {
  isCheckingAuth: boolean;
  children: React.ReactNode;
}

export function AuthLayout({ isCheckingAuth, children }: AuthLayoutProps) {
  if (isCheckingAuth) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-gray-900 dark:to-gray-800">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-gray-900 dark:to-gray-800 p-4">
      {children}
    </div>
  );
}
