"use client";

import { useCallback, useRef, useState } from "react";
import { sendMessage } from "@/lib/api";
import type { ChatMessage, Citation } from "@/lib/types";

export function useChat(initialThreadId?: string) {
  const [threadId, setThreadId] = useState<string | undefined>(initialThreadId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      setError(null);
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: content.trim(),
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const response = await sendMessage(content.trim(), threadId);

        // Update threadId on first message
        if (!threadId) setThreadId(response.thread_id);

        const assistantMsg: ChatMessage = {
          id: response.message_id,
          role: "assistant",
          content: response.answer,
          intent: response.intent,
          citations: response.citations,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      } catch (err: any) {
        const msg = err?.response?.data?.detail ?? err?.message ?? "Something went wrong";
        setError(msg);
        // Remove the optimistic user message on error
        setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
      } finally {
        setIsLoading(false);
      }
    },
    [threadId, isLoading]
  );

  const reset = useCallback(() => {
    setMessages([]);
    setThreadId(undefined);
    setError(null);
  }, []);

  return { threadId, messages, isLoading, error, send, reset };
}
