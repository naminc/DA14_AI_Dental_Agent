"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { TabsContent } from "@/components/ui/tabs";
import { Check, Mail, Loader2 } from "lucide-react";
import type { UserInfo } from "@/stores/use-auth-store";
import { useUpdateProfileForm } from "@/hooks/use-update-profile";

// ==========================================
// PROPS
// ==========================================
interface AccountProfileTabProps {
  user: UserInfo | null;
}

// ==========================================
// PROFILE TAB COMPONENT
// ==========================================
export function AccountProfileTab({ user }: AccountProfileTabProps) {
  const {
    isLoading,
    isSuccess,
    fullName,
    errors,
    isFormValid,
    isUnchanged,
    handleSubmit,
    handleChange,
  } = useUpdateProfileForm(user);

  return (
    <TabsContent
      value="profile"
      className="mt-0 px-6 pb-6 pt-4 space-y-5 data-[state=inactive]:hidden"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Full Name */}
        <div className="space-y-2">
          <Label htmlFor="account-fullname" className="text-sm font-medium">
            Họ và tên
          </Label>
          <Input
            id="account-fullname"
            value={fullName}
            onChange={(e) => handleChange(e.target.value)}
            placeholder="Nhập họ và tên của bạn"
          />
          {errors.fullName && (
            <p className="text-xs text-destructive">{errors.fullName}</p>
          )}
        </div>

        {/* Email (read-only) */}
        <div className="space-y-2">
          <Label htmlFor="account-email" className="text-sm font-medium">
            Email
          </Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              id="account-email"
              value={user?.email || ""}
              disabled
              className="pl-9 opacity-50 cursor-not-allowed"
            />
          </div>
          <p className="text-xs text-muted-foreground italic">
            Email không thể thay đổi
          </p>
        </div>

        {/* General error */}
        {errors.general && (
          <p className="text-xs text-destructive text-center">{errors.general}</p>
        )}

        {/* Save Button */}
        <Button
          type="submit"
          disabled={!isFormValid || isUnchanged || isLoading}
          className="w-full h-10"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 size-4 animate-spin" />
              Đang lưu...
            </>
          ) : isSuccess ? (
            <>
              <Check className="mr-2 size-4" />
              Đã lưu thay đổi
            </>
          ) : (
            "Lưu thay đổi"
          )}
        </Button>
      </form>
    </TabsContent>
  );
}
