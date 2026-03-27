import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  TooltipProvider,
} from "@/components/ui/tooltip";
import { Moon, Sun } from "lucide-react";

interface ChatHeaderProps {
  title: string;
  isDark: boolean;
  onToggleTheme: () => void;
}

// Chat Header Component
export function ChatHeader({ title, isDark, onToggleTheme }: ChatHeaderProps) {
  return (
    <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b bg-background px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-2 h-4" />
      <div className="flex flex-1 items-center gap-2 min-w-0">
        <span className="text-sm font-medium truncate">{title}</span>
      </div>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" onClick={onToggleTheme}>
              {isDark ? (
                <Sun className="size-4" />
              ) : (
                <Moon className="size-4" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {isDark ? "Chế độ sáng" : "Chế độ tối"}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </header>
  );
}
