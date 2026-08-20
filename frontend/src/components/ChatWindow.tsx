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
        {/* Logo mark */}
        <div className="mb-6 h-14 w-14 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
          <span className="text-2xl font-bold text-white">R</span>
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">RAGentic — AWS Cloud Assistant</h2>
        <p className="text-sm text-white/40 max-w-md mb-10 leading-relaxed">
          Ask questions about AWS services (EC2, S3, IAM, VPC, ECS, CloudWatch, Lambda, and more).
          Answers are strictly grounded in indexed AWS documentation and cite verified sources.
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
