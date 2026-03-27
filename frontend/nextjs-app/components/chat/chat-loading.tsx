import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot } from "lucide-react";

// Chat Loading Component
export function ChatLoading() {
  return (
    <div className="flex gap-3">
      <Avatar className="h-8 w-8 shrink-0 bg-primary text-primary-foreground">
        <AvatarFallback className="bg-primary text-primary-foreground">
          <Bot className="h-4 w-4" />
        </AvatarFallback>
      </Avatar>
      <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/60 [animation-delay:-0.3s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/60 [animation-delay:-0.15s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/60" />
          </div>
        </div>
      </div>
    </div>
  );
}
