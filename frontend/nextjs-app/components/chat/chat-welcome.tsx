import { Button } from "@/components/ui/button";
import { ToothIcon } from "@/components/icons/tooth-icon";
import { Sparkles } from "lucide-react";
import { APP_CONFIG, SUGGESTIONS } from "@/lib/constants";

// Props
interface ChatWelcomeProps {
  onSelectSuggestion: (suggestion: string) => void;
}

// Chat Welcome Component
export function ChatWelcome({ onSelectSuggestion }: ChatWelcomeProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 md:py-24">
      <div className="relative mb-8">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl border bg-background shadow-sm">
          <ToothIcon className="h-8 w-8" />
        </div>
        <div className="absolute -right-2 -top-2 flex h-7 w-7 items-center justify-center rounded-lg bg-primary shadow-sm">
          <Sparkles className="h-3.5 w-3.5 text-primary-foreground" />
        </div>
      </div>

      <h2 className="mb-3 text-center text-xl font-semibold text-balance md:text-2xl">
        Xin chào! Tôi là trợ lý nha khoa {APP_CONFIG.NAME}
      </h2>
      <p className="mb-8 max-w-md text-center text-muted-foreground text-balance">
        Hãy đặt câu hỏi về sức khỏe răng miệng của bạn!
      </p>

      {/* Suggestions */}
      <div className="flex flex-wrap justify-center gap-2">
        {SUGGESTIONS.map((suggestion) => (
          <Button
            key={suggestion}
            variant="outline"
            size="sm"
            className="h-auto rounded-full px-4 py-2 text-sm"
            onClick={() => onSelectSuggestion(suggestion)}
          >
            {suggestion}
          </Button>
        ))}
      </div>
    </div>
  );
}
