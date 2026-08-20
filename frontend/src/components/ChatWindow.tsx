"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { BookOpen, Zap, Search, Wrench } from "lucide-react";

const EXAMPLE_PROMPTS = [
  { icon: Search, text: "What is the main contribution of the Attention Is All You Need paper?" },
  { icon: BookOpen, text: "Explain how BERT uses masked language modelling" },
  { icon: Zap, text: "Summarise the key findings from the RAG paper by Lewis et al." },
  { icon: Wrench, text: "Calculate 1024 * 768" },
];

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onExampleClick: (text: string) => void;
}

export function ChatWindow({ messages, isLoading, onExampleClick }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-8 py-16 text-center">
        {/* Logo mark */}
        <div className="mb-6 h-14 w-14 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
          <span className="text-2xl font-bold text-white">R</span>
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">RAGentic</h2>
        <p className="text-sm text-white/40 max-w-sm mb-10 leading-relaxed">
          Ask questions about your indexed documents. I&apos;ll retrieve the most relevant
          context and cite my sources.
        </p>

        {/* Example prompts */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-xl">
          {EXAMPLE_PROMPTS.map(({ icon: Icon, text }) => (
            <button
              key={text}
              onClick={() => onExampleClick(text)}
              className="flex items-start gap-3 rounded-xl border border-white/8 bg-white/3 hover:bg-white/7 hover:border-white/15 p-3.5 text-left transition-all duration-150 group"
            >
              <Icon size={15} className="text-violet-400 flex-shrink-0 mt-0.5" />
              <span className="text-xs text-white/55 group-hover:text-white/75 leading-snug">{text}</span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-y-auto py-4 space-y-1 scrollbar-thin">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {isLoading && <ThinkingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
