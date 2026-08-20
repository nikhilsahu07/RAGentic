"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/lib/types";
import { CitationBadge } from "./CitationBadge";
import { User } from "lucide-react";

const INTENT_META: Record<
  string,
  { label: string; dotColor: string; textColor: string; borderColor: string; bgColor: string }
> = {
  retrieve: {
    label: "retrieved",
    dotColor: "var(--teal)",
    textColor: "var(--teal)",
    borderColor: "var(--teal-soft-border)",
    bgColor: "var(--teal-soft)",
  },
  direct: {
    label: "direct",
    dotColor: "var(--slate)",
    textColor: "var(--slate)",
    borderColor: "var(--slate-soft-border)",
    bgColor: "var(--slate-soft)",
  },
  tool: {
    label: "tool used",
    dotColor: "var(--accent)",
    textColor: "var(--accent-text)",
    borderColor: "var(--accent-soft-border)",
    bgColor: "var(--accent-soft)",
  },
  declined: {
    label: "declined",
    dotColor: "var(--red)",
    textColor: "var(--red)",
    borderColor: "var(--red-soft-border)",
    bgColor: "var(--red-soft)",
  },
};

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const intentMeta = message.intent ? INTENT_META[message.intent] : null;

  if (isUser) {
    return (
      <div className="flex justify-end px-4 py-2">
        <div className="flex items-start gap-2.5 max-w-[75%]">
          <div className="rounded-lg rounded-tr-sm border border-[var(--border-hover)] bg-[var(--surface-raised)] px-4 py-3">
            <p className="text-sm text-[var(--text-primary)] leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          </div>
          <div className="h-7 w-7 flex-shrink-0 rounded-md border border-[var(--border-hover)] bg-[var(--surface)] flex items-center justify-center mt-0.5">
            <User size={13} className="text-[var(--text-secondary)]" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 px-4 py-2">
      {/* Avatar */}
      <div className="h-7 w-7 flex-shrink-0 rounded-md border border-[var(--border-hover)] bg-[var(--surface)] flex items-center justify-center mt-0.5">
        <span className="font-mono-ui text-[10px] font-semibold text-[var(--accent-text)]">R</span>
      </div>

      <div className="flex-1 min-w-0 max-w-[80%]">
        {/* Message card */}
        <div
          className={`rounded-lg rounded-tl-sm px-4 py-3 border ${message.intent === "declined"
              ? "bg-[var(--red-soft)] border-[var(--red-soft-border)]"
              : "bg-[var(--surface)] border-[var(--border)]"
            }`}
        >
          <div className="prose prose-invert prose-sm max-w-none text-[var(--text-primary)]/90 leading-relaxed">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        </div>

        {/* Intent badge + citations */}
        <div className="mt-2 flex items-start gap-2 flex-wrap">
          {intentMeta && (
            <span
              className="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono-ui text-[10px] font-medium"
              style={{
                color: intentMeta.textColor,
                borderColor: intentMeta.borderColor,
                backgroundColor: intentMeta.bgColor,
              }}
            >
              <span
                className="h-1.5 w-1.5 rounded-full"
                style={{ backgroundColor: intentMeta.dotColor }}
              />
              {intentMeta.label}
            </span>
          )}
        </div>

        {message.citations && message.citations.length > 0 && (
          <CitationBadge citations={message.citations} />
        )}
      </div>
    </div>
  );
}