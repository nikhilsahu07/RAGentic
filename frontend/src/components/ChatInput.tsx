"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowUp, Square } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, isLoading, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea up to 6 lines (~144px)
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 144)}px`;
  }, [value]);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue("");
    // Reset height
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }, [value, isLoading, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-[var(--border)] bg-[var(--surface)] px-4 py-4">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-2 rounded-xl border border-[var(--border-hover)] bg-[var(--bg)] px-4 py-3 focus-within:border-[var(--accent)] transition-colors duration-150">
          <textarea
            ref={textareaRef}
            id="chat-input"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about AWS services, VPC, EC2, IAM, S3, ECS, Lambda... (Ctrl+Enter to send)"
            rows={1}
            disabled={isLoading || disabled}
            className="flex-1 resize-none bg-transparent text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none leading-relaxed disabled:opacity-50"
          />
          <button
            id="send-btn"
            onClick={handleSend}
            disabled={!value.trim() || isLoading || disabled}
            aria-label={isLoading ? "Stop generating" : "Send message"}
            className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:bg-[var(--surface-raised)] disabled:cursor-not-allowed transition-colors duration-150"
          >
            {isLoading ? (
              <Square
                size={11}
                className={value.trim() ? "text-[#171310] fill-[#171310]" : "text-[var(--text-tertiary)] fill-[var(--text-tertiary)]"}
              />
            ) : (
              <ArrowUp
                size={14}
                strokeWidth={2.5}
                className={value.trim() ? "text-[#171310]" : "text-[var(--text-tertiary)]"}
              />
            )}
          </button>
        </div>
        <p className="mt-2 text-center text-[10px] text-[var(--text-tertiary)]">
          Ctrl+Enter to send · Answers cite retrieved AWS document chunks
        </p>
      </div>
    </div>
  );
}