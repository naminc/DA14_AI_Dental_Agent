import { useState } from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  BookOpen,
  ChevronDown,
  Search,
  Bot,
  User,
  Copy,
  Check,
  FileDown,
} from "lucide-react";
import type { Message } from "@/hooks/use-dental-chat";
import { exportConsultationPdf } from "@/lib/export-pdf";

// ==========================================
// UTILITY FUNCTIONS
// ==========================================
const normalizeSourceUrl = (rawSource: string) =>
  rawSource.startsWith("http")
    ? rawSource
    : `https://${rawSource.replace(/^\/+/, "")}`;

const getSourceSiteLabel = (rawSource: string) => {
  try {
    return new URL(normalizeSourceUrl(rawSource)).hostname
      .toLowerCase()
      .replace(/^www\./, "");
  } catch {
    return "";
  }
};

// ==========================================
// COMPONENT
// ==========================================
interface ChatMessageProps {
  message: Message;
  index: number;
  isSourceOpen: boolean;
  onSourceToggle: (open: boolean) => void;
  previousMessage?: Message;
}

export function ChatMessage({
  message,
  index,
  isSourceOpen,
  onSourceToggle,
  previousMessage,
}: ChatMessageProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportPdf = () => {
    const question = previousMessage?.role === "user"
      ? previousMessage.content
      : "Không rõ câu hỏi";

    exportConsultationPdf({
      question,
      answer: message.content,
      sources: message.sources,
    });
  };

  const sourceSites = message.sources
    ? Array.from(
        new Set(
          message.sources
            .map((source) => getSourceSiteLabel(source.source))
            .filter(Boolean),
        ),
      )
    : [];

  const isAssistant = message.role === "assistant";
  // Kiểm tra trạng thái đang chờ stream: là Assistant và nội dung trống
  const isWaitingForStream = isAssistant && message.content === "";

  return (
    <div
      className={cn(
        "flex gap-3",
        message.role === "user" ? "flex-row-reverse" : "flex-row",
      )}
    >
      {/* Avatar Section */}
      <Avatar
        className={cn(
          "h-8 w-8 shrink-0",
          isAssistant ? "bg-primary text-primary-foreground" : "bg-muted",
        )}
      >
        <AvatarFallback
          className={cn(
            isAssistant
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground",
          )}
        >
          {isAssistant ? (
            <Bot className="h-4 w-4" />
          ) : (
            <User className="h-4 w-4" />
          )}
        </AvatarFallback>
      </Avatar>

      <div
        className={cn(
          "flex max-w-[80%] flex-col gap-2",
          message.role === "user" ? "items-end" : "items-start",
        )}
      >
        {/* Chat Bubble Section */}
        <div
          className={cn(
            "overflow-hidden rounded-2xl",
            message.role === "user"
              ? "rounded-tr-sm bg-primary text-primary-foreground"
              : "rounded-tl-sm bg-muted",
          )}
        >
          <div className="px-4 py-3">
            {isWaitingForStream ? (
              /* Hiệu ứng Loading khi bắt đầu Stream */
              <div className="flex h-5 items-center gap-1 px-1">
                <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/60 [animation-delay:-0.3s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/60 [animation-delay:-0.15s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/60" />
              </div>
            ) : (
              /* Hiển thị văn bản thuần, giữ nguyên dấu xuống dòng và khoảng trắng */
              <p className="whitespace-pre-wrap text-sm leading-normal">
                {message.content}
              </p>
            )}
          </div>
        </div>

        {/* Action Toolbar — chỉ hiện cho assistant khi đã có nội dung */}
        {isAssistant && !isWaitingForStream && message.content && (
          <TooltipProvider delayDuration={300}>
            <div className="flex items-center gap-0.5">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-muted-foreground hover:text-foreground"
                    onClick={handleCopy}
                  >
                    {copied ? (
                      <Check className="h-3.5 w-3.5 text-green-500" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">
                  {copied ? "Đã sao chép!" : "Sao chép"}
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-muted-foreground hover:text-foreground"
                    onClick={handleExportPdf}
                  >
                    <FileDown className="h-3.5 w-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">
                  Xuất PDF
                </TooltipContent>
              </Tooltip>
            </div>
          </TooltipProvider>
        )}

        {/* Sources Panel Section */}
        {message.sources && message.sources.length > 0 && (
          <Collapsible
            open={isSourceOpen}
            onOpenChange={onSourceToggle}
            className="w-full"
          >
            <Card className="overflow-hidden border-dashed">
              <CollapsibleTrigger asChild>
                <div className="cursor-pointer py-1.5 px-3 transition-colors hover:bg-muted/50">
                  <div className="flex items-center gap-2">
                    <BookOpen className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-xs font-medium text-muted-foreground">
                      Nguồn tham chiếu ({message.sources.length})
                    </span>
                    {sourceSites.length >= 1 && (
                      <div className="flex flex-1 flex-wrap items-center gap-1">
                        {sourceSites.map((site) => (
                          <Badge
                            key={site}
                            variant="outline"
                            className="px-1.5 py-0 text-[10px] text-muted-foreground"
                          >
                            {site}
                          </Badge>
                        ))}
                      </div>
                    )}
                    {sourceSites.length < 1 && <span className="flex-1" />}
                    <ChevronDown
                      className={cn(
                        "h-3.5 w-3.5 text-muted-foreground transition-transform duration-200",
                        isSourceOpen && "rotate-180",
                      )}
                    />
                  </div>
                </div>
              </CollapsibleTrigger>

              <CollapsibleContent>
                <Separator />
                <CardContent className="p-3">
                  {/* Truy vấn đã tối ưu (Rewritten Query) */}
                  {message.rewrittenQuery && (
                    <div className="mb-3 rounded-lg bg-muted p-3">
                      <div className="mb-1 flex items-center gap-2">
                        <Search className="h-3 w-3 text-muted-foreground" />
                        <span className="text-xs font-medium text-muted-foreground">
                          Truy vấn tối ưu
                        </span>
                      </div>
                      <p className="text-sm">{message.rewrittenQuery}</p>
                    </div>
                  )}

                  {/* Danh sách các tài liệu trích xuất */}
                  <div className="flex flex-col gap-1.5">
                    {message.sources.map((src, i) => (
                      <div key={i} className="rounded-md border px-3 py-2">
                        <p className="text-sm font-medium">
                          [{i + 1}] {src.title || "Tài liệu"}
                        </p>

                        <div className="flex flex-wrap items-center gap-1">
                          <Badge variant="secondary" className="text-[10px]">
                            {src.metadata.disease}
                          </Badge>
                        </div>

                        <a
                          href={normalizeSourceUrl(src.source)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-1 block text-[11px] text-muted-foreground underline underline-offset-2 break-all hover:text-foreground"
                        >
                          {normalizeSourceUrl(src.source)}
                        </a>

                        <Collapsible>
                          <CollapsibleTrigger className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
                            <span>Đọc đoạn trích xuất</span>
                            <ChevronDown className="h-3 w-3" />
                          </CollapsibleTrigger>
                          <CollapsibleContent>
                            <p className="mt-1 rounded-lg bg-muted p-1.5 text-xs leading-relaxed text-muted-foreground">
                              {src.content}
                            </p>
                          </CollapsibleContent>
                        </Collapsible>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Card>
          </Collapsible>
        )}
      </div>
    </div>
  );
}
