import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import {
  Trash2,
  MessageSquare,
  Info,
  User,
  ChevronsUpDown,
  History,
  Plus,
  LogOut,
  UserCog,
} from "lucide-react";
import { ToothIcon } from "@/components/icons/tooth-icon";
import type { ChatSession } from "@/hooks/use-dental-chat";
import type { UserInfo } from "@/stores/use-auth-store";

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  user: UserInfo | null;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (e: React.MouseEvent, id: string) => void;
  onClearAllChat: () => void;
  onAboutOpen: () => void;
  onAccountOpen: () => void;
  onLogout: () => void;
}

export function ChatSidebar({
  sessions,
  activeSessionId,
  user,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onClearAllChat,
  onAboutOpen,
  onAccountOpen,
  onLogout,
}: ChatSidebarProps) {
  return (
    <Sidebar collapsible="icon" className="border-r">
      {/* ================= SIDEBAR HEADER ================= */}
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              size="lg"
              className="cursor-default hover:bg-transparent"
            >
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                <ToothIcon className="size-4" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">Dental AI</span>
                <span className="truncate text-xs text-muted-foreground">
                  v1.0.0
                </span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      {/* ================= SIDEBAR CONTENT ================= */}
      <SidebarContent>
        {/* New Chat Button */}
        <SidebarGroup>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                onClick={onNewChat}
                tooltip="Cuộc trò chuyện mới"
                className="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground"
              >
                <Plus className="size-4" />
                <span className="text-sm">Cuộc trò chuyện mới</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>

        {/* Chat History List */}
        <SidebarGroup className="flex-1">
          <SidebarGroupLabel>
            <History className="size-4 mr-2" />
            Lịch sử trò chuyện
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {sessions.length === 0 ? (
                <div className="px-3 py-6 text-center group-data-[collapsible=icon]:hidden">
                  <MessageSquare className="mx-auto mb-2 size-8 text-muted-foreground/50" />
                  <p className="text-xs text-muted-foreground">
                    Chưa có cuộc hội thoại nào
                  </p>
                </div>
              ) : (
                sessions.map((session) => (
                  <SidebarMenuItem
                    key={session.id}
                    className="group relative"
                  >
                    <SidebarMenuButton
                      onClick={() => onSelectSession(session.id)}
                      isActive={activeSessionId === session.id}
                      tooltip={session.title}
                    >
                      <MessageSquare className="size-4 shrink-0" />
                      <span className="truncate pr-6">{session.title}</span>
                    </SidebarMenuButton>

                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute right-1 top-1/2 h-6 w-6 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={(e) => onDeleteSession(e, session.id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </SidebarMenuItem>
                ))
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {/* ================= SIDEBAR FOOTER ================= */}
      <SidebarFooter>
        {/* Clear All Chat Button */}
        <div className="mx-2 group-data-[collapsible=icon]:hidden">
          <Button
            variant="outline"
            size="sm"
            onClick={onClearAllChat}
            className="w-full border-destructive/35 text-destructive/78 hover:bg-destructive/10 hover:text-destructive hover:border-destructive/50 font-normal dark:border-destructive/70 dark:text-destructive dark:hover:border-destructive dark:hover:bg-destructive/15"
          >
            <Trash2 className="size-3.5" />
            Xóa lịch sử trò chuyện
          </Button>
        </div>

        {/* Disclaimer Notice */}
        <div className="mx-2 mb-3 rounded-lg border border-dashed border-foreground/50 p-3 group-data-[collapsible=icon]:hidden">
          <p className="text-xs leading-relaxed text-muted-foreground">
            <span className="font-medium text-foreground">Lưu ý:</span> Nội
            dung truy xuất mang tính tham khảo, không thay thế chỉ định y khoa
            chính thức từ bác sĩ.
          </p>
        </div>

        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                >
                  <Avatar className="h-8 w-8 rounded-lg">
                    <AvatarImage src="/placeholder-avatar.jpg" alt="User" />
                    <AvatarFallback className="rounded-lg">
                      <User className="size-4" />
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold">{user?.fullName || "User"}</span>
                    <span className="truncate text-xs text-muted-foreground">
                      {user?.email || ""}
                    </span>
                  </div>
                  <ChevronsUpDown className="ml-auto size-4" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
                side="bottom"
                align="end"
                sideOffset={4}
              >
                <DropdownMenuItem onClick={onAccountOpen}>
                  <UserCog className="mr-2 size-4" />
                  Tài khoản
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onAboutOpen}>
                  <Info className="mr-2 size-4" />
                  Giới thiệu
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onLogout}
                  className="text-destructive focus:text-destructive"
                >
                  <LogOut className="mr-2 size-4" />
                  Đăng xuất
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
