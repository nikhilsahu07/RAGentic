"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { Cloud, Shield, Network, Wrench } from "lucide-react";

const EXAMPLE_PROMPTS = [
  { icon: Network, text: "How do VPC subnets, route tables, and NAT Gateways work together?" },
  { icon: Cloud, text: "Explain Amazon S3 storage classes, versioning, and lifecycle transition rules" },
  { icon: Shield, text: "What are the core principles of IAM policies, roles, and least-privilege evaluation?" },
  { icon: Wrench, text: "Calculate (64 * 1024) / 8" },
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
        {/* Mark */}
        <div className="mb-6 h-12 w-12 rounded-lg border border-[var(--border-hover)] bg-[var(--surface)] flex items-center justify-center">
          <span className="font-mono-ui text-lg font-semibold text-[var(--accent-text)]">R</span>
        </div>
        <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
          RAGentic — AWS Cloud Assistant
        </h2>
        <p className="text-sm text-[var(--text-secondary)] max-w-md mb-10 leading-relaxed">
          Ask questions about AWS services (EC2, S3, IAM, VPC, ECS, CloudWatch, Lambda, and more).
          Answers are strictly grounded in indexed AWS documentation and cite verified sources.
        </p>

        {/* Example prompts */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-xl">
          {EXAMPLE_PROMPTS.map(({ icon: Icon, text }) => (
            <button
              key={text}
              onClick={() => onExampleClick(text)}
              className="flex items-start gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] hover:border-[var(--border-hover)] p-3.5 text-left transition-colors duration-150"
            >
              <Icon size={14} className="text-[var(--accent-text)] flex-shrink-0 mt-0.5" />
              <span className="text-xs text-[var(--text-secondary)] leading-snug">{text}</span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-y-auto py-4 space-y-1">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {isLoading && <ThinkingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}