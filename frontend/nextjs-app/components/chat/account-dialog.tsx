"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Pencil, Shield, LogOut } from "lucide-react";
import type { UserInfo } from "@/stores/use-auth-store";

import { AccountProfileTab } from "./account-profile-tab";
import { AccountSecurityTab } from "./account-security-tab";

// ==========================================
// PROPS
// ==========================================
interface AccountDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user: UserInfo | null;
  onLogout: () => void;
}

// ==========================================
// ACCOUNT DIALOG COMPONENT
// ==========================================
export function AccountDialog({ open, onOpenChange, user, onLogout }: AccountDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[540px] p-0 gap-0 overflow-hidden">
        {/* ============ HEADER ============ */}
        <div className="shrink-0 border-b bg-background px-6 pt-6 pb-5">
          <DialogHeader className="mb-0">
            <DialogTitle className="text-lg font-semibold tracking-tight">
              Cài đặt tài khoản
            </DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              Quản lý thông tin cá nhân và bảo mật tài khoản
            </DialogDescription>
          </DialogHeader>

          {/* User card */}
          <div className="mt-4 flex items-center gap-3 rounded-xl border bg-muted/40 p-3">
            <Avatar className="size-11 rounded-xl shadow-sm">
              <AvatarImage src="/placeholder-avatar.jpg" alt="User" />
              <AvatarFallback className="rounded-xl bg-primary text-primary-foreground text-sm font-bold">
                {user?.fullName
                  ?.split(" ")
                  .map((w) => w[0])
                  .join("")
                  .slice(0, 2)
                  .toUpperCase() || "U"}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold truncate">
                {user?.fullName || "User"}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {user?.email || ""}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onLogout}
              tabIndex={-1}
              className="shrink-0 size-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10 focus-visible:ring-0 focus-visible:ring-offset-0"
            >
              <LogOut className="size-4" />
            </Button>
          </div>
        </div>

        {/* ============ TABS ============ */}
        <Tabs defaultValue="profile" className="w-full">
          <div className="shrink-0 px-6 pt-3 pb-1">
            <TabsList className="w-full h-10">
              <TabsTrigger
                value="profile"
                className="flex-1 gap-2 text-sm focus-visible:ring-0 focus-visible:border-transparent focus-visible:outline-none"
              >
                <Pencil className="size-3.5" />
                Tài khoản
              </TabsTrigger>
              <TabsTrigger
                value="security"
                className="flex-1 gap-2 text-sm focus-visible:ring-0 focus-visible:border-transparent focus-visible:outline-none"
              >
                <Shield className="size-3.5" />
                Bảo mật
              </TabsTrigger>
            </TabsList>
          </div>

          {/* Scrollable content */}
          <div className="overflow-y-auto max-h-[50vh]">
            <AccountProfileTab user={user} />
            <AccountSecurityTab />
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
