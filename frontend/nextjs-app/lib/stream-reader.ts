import type { Source } from "@/hooks/use-dental-chat";

// Type Definitions
export interface StreamCallbacks {
  onToken: (accumulated: string) => void;
  onDone: (sources: Source[], rewrittenQuery: string) => void;
}

/**
 * Đọc SSE stream từ chat API và gọi callback tương ứng.
 * - onToken: gọi mỗi khi nhận được text chunk, truyền vào chuỗi đã tích lũy
 * - onDone: gọi khi stream kết thúc, truyền vào sources + rewrittenQuery
 */
export async function readChatStream(
  response: Response,
  { onToken, onDone }: StreamCallbacks,
): Promise<void> {
  const reader = response.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let accumulated = "";
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const dataStr = line.slice(6).trim();
      if (!dataStr) continue;

      try {
        const data = JSON.parse(dataStr);

        if (data.token) {
          accumulated += data.token;
          onToken(accumulated);
        } else if (data.done) {
          onDone(data.sources ?? [], data.rewritten_query ?? "");
        }
      } catch (e) {
        console.error("Lỗi parse JSON chunk:", e, dataStr);
      }
    }
  }
}
