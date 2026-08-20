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
    <div className="border-t border-white/5 bg-[#0d0d0f] px-4 py-4">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 focus-within:border-violet-500/50 focus-within:bg-white/7 transition-all duration-150">
          <textarea
            ref={textareaRef}
            id="chat-input"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask something about your documents… (Ctrl+Enter to send)"
            rows={1}
            disabled={isLoading || disabled}
            className="flex-1 resize-none bg-transparent text-sm text-white placeholder-white/25 focus:outline-none leading-relaxed disabled:opacity-50"
          />
          <button
            id="send-btn"
            onClick={handleSend}
            disabled={!value.trim() || isLoading || disabled}
            className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-150 active:scale-95"
          >
            {isLoading ? (
              <Square size={12} className="text-white fill-white" />
            ) : (
              <ArrowUp size={14} className="text-white" strokeWidth={2.5} />
            )}
          </button>
        </div>
        <p className="mt-2 text-center text-[10px] text-white/20">
          Ctrl+Enter to send · Answers cite retrieved document chunks
        </p>
      </div>
    </div>
  );
}
