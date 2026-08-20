"use client";

import { Plus, MessageCircle, Clock } from "lucide-react";
import type { ThreadSummary } from "@/lib/types";

interface SidebarProps {
  threads: ThreadSummary[];
  activeThreadId?: string;
  onNewChat: () => void;
  onSelectThread: (threadId: string) => void;
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function Sidebar({ threads, activeThreadId, onNewChat, onSelectThread }: SidebarProps) {
  return (
    <aside className="flex h-full w-72 flex-col border-r border-[var(--border)] bg-[var(--surface)]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-[var(--border)]">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md border border-[var(--border-hover)] bg-[var(--surface-raised)]">
            <span className="font-mono-ui text-[11px] font-semibold text-[var(--accent-text)]">R</span>
          </div>
          <span className="text-[13px] font-semibold text-[var(--text-primary)] tracking-tight">
            RAGentic
          </span>
        </div>
        <button
          id="new-chat-btn"
          onClick={onNewChat}
          className="flex items-center gap-1.5 rounded-md bg-[var(--accent)] hover:bg-[var(--accent-hover)] px-2.5 py-1.5 text-xs font-medium text-[#171310] transition-colors duration-150"
        >
          <Plus size={13} strokeWidth={2.5} />
          New
        </button>
      </div>

      {/* Thread list */}
      <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
        {threads.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center px-4">
            <MessageCircle size={22} className="text-[var(--text-tertiary)] mb-3" />
            <p className="text-xs text-[var(--text-secondary)]">No conversations yet</p>
            <p className="text-xs text-[var(--text-tertiary)] mt-1">
              Start a new chat above
            </p>
          </div>
        ) : (
          threads.map((t) => {
            const active = activeThreadId === t.thread_id;
            return (
              <button
                key={t.thread_id}
                id={`thread-${t.thread_id.slice(0, 8)}`}
                onClick={() => onSelectThread(t.thread_id)}
                className={`w-full text-left rounded-md px-3 py-2.5 border transition-colors duration-100 ${active
                    ? "bg-[var(--surface-raised)] border-[var(--border-hover)] text-[var(--text-primary)]"
                    : "border-transparent text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)]"
                  }`}
              >
                <span className="block text-xs font-medium leading-snug line-clamp-2">
                  {t.title || "New conversation"}
                </span>
                <div className="flex items-center gap-1.5 mt-1.5">
                  <Clock size={10} className="text-[var(--text-tertiary)]" />
                  <span className="font-mono-ui text-[10px] text-[var(--text-tertiary)]">
                    {timeAgo(t.updated_at)}
                  </span>
                  <span className="font-mono-ui text-[10px] text-[var(--text-tertiary)] ml-auto">
                    {t.message_count} msg{t.message_count !== 1 ? "s" : ""}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </nav>
    </aside>
  );
}