"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/lib/types";
import { CitationBadge } from "./CitationBadge";
import { Bot, User, Zap, Search, Wrench, AlertTriangle } from "lucide-react";

const INTENT_BADGES: Record<string, { label: string; Icon: any; className: string }> = {
  retrieve: {
    label: "Retrieved",
    Icon: Search,
    className: "text-violet-400 bg-violet-500/10 border-violet-500/25",
  },
  direct: {
    label: "Direct",
    Icon: Zap,
    className: "text-sky-400 bg-sky-500/10 border-sky-500/25",
  },
  tool: {
    label: "Tool",
    Icon: Wrench,
    className: "text-amber-400 bg-amber-500/10 border-amber-500/25",
  },
  declined: {
    label: "Declined",
    Icon: AlertTriangle,
    className: "text-red-400 bg-red-500/10 border-red-500/25",
  },
};

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const intentMeta = message.intent ? INTENT_BADGES[message.intent] : null;

  if (isUser) {
    return (
      <div className="flex justify-end px-4 py-2">
        <div className="flex items-start gap-2.5 max-w-[75%]">
          <div className="rounded-2xl rounded-tr-sm bg-violet-600 px-4 py-3 shadow-lg">
            <p className="text-sm text-white leading-relaxed whitespace-pre-wrap">{message.content}</p>
          </div>
          <div className="h-7 w-7 flex-shrink-0 rounded-full bg-white/10 border border-white/10 flex items-center justify-center mt-0.5">
            <User size={13} className="text-white/70" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 px-4 py-2">
      {/* Avatar */}
      <div className="h-7 w-7 flex-shrink-0 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center mt-0.5">
        <Bot size={13} className="text-white" />
      </div>

      <div className="flex-1 min-w-0 max-w-[80%]">
        {/* Message card */}
        <div
          className={`rounded-2xl rounded-tl-sm px-4 py-3 border shadow-sm ${
            message.intent === "declined"
              ? "bg-red-950/30 border-red-500/20"
              : "bg-white/5 border-white/8"
          }`}
        >
          <div className="prose prose-invert prose-sm max-w-none text-white/85 leading-relaxed">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        </div>

        {/* Intent badge + citations */}
        <div className="mt-2 flex items-start gap-2 flex-wrap">
          {intentMeta && (
            <span
              className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium ${intentMeta.className}`}
            >
              <intentMeta.Icon size={9} />
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
