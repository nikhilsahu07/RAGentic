"use client";

import { MessageSquarePlus, MessageCircle, Clock } from "lucide-react";
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
    <aside className="flex h-full w-72 flex-col border-r border-white/5 bg-[#0d0d0f]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-5 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
            <span className="text-xs font-bold text-white">R</span>
          </div>
          <span className="text-sm font-semibold text-white tracking-tight">RAGentic</span>
        </div>
        <button
          id="new-chat-btn"
          onClick={onNewChat}
          className="flex items-center gap-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 px-3 py-1.5 text-xs font-medium text-white transition-colors duration-150"
        >
          <MessageSquarePlus size={13} />
          New
        </button>
      </div>

      {/* Thread list */}
      <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5 scrollbar-thin">
        {threads.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <MessageCircle size={28} className="text-white/20 mb-3" />
            <p className="text-xs text-white/30">No conversations yet</p>
            <p className="text-xs text-white/20 mt-1">Start a new chat above</p>
          </div>
        ) : (
          threads.map((t) => (
            <button
              key={t.thread_id}
              id={`thread-${t.thread_id.slice(0, 8)}`}
              onClick={() => onSelectThread(t.thread_id)}
              className={`w-full text-left rounded-lg px-3 py-2.5 transition-colors duration-100 group ${
                activeThreadId === t.thread_id
                  ? "bg-white/10 text-white"
                  : "text-white/60 hover:bg-white/5 hover:text-white/80"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-xs font-medium leading-snug line-clamp-2 flex-1">
                  {t.title || "New conversation"}
                </span>
              </div>
              <div className="flex items-center gap-1.5 mt-1.5">
                <Clock size={10} className="text-white/25" />
                <span className="text-[10px] text-white/30">{timeAgo(t.updated_at)}</span>
                <span className="text-[10px] text-white/20 ml-auto">
                  {t.message_count} msg{t.message_count !== 1 ? "s" : ""}
                </span>
              </div>
            </button>
          ))
        )}
      </nav>
    </aside>
  );
}
