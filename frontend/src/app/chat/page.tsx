"use client";

import { useCallback, useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { ChatWindow } from "@/components/ChatWindow";
import { ChatInput } from "@/components/ChatInput";
import { useChat } from "@/hooks/useChat";
import { useThreads } from "@/hooks/useThreads";
import { fetchThread } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";
import { AlertCircle, Menu, X } from "lucide-react";

export default function ChatPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { threads, refresh: refreshThreads } = useThreads();
  const { threadId, messages, isLoading, error, send, reset } = useChat();

  // Refresh sidebar after each send
  const handleSend = useCallback(
    async (message: string) => {
      await send(message);
      refreshThreads();
    },
    [send, refreshThreads]
  );

  // Load a historical thread from sidebar
  const handleSelectThread = useCallback(async (tid: string) => {
    try {
      const detail = await fetchThread(tid);
      // We reset and manually inject — useChat doesn't expose setMessages externally
      // So we use a page-level state for historical view
      setHistoryMessages(detail.messages);
      setViewingHistory(true);
      setHistoryThreadId(tid);
    } catch {
      // Silently ignore
    }
  }, []);

  const [viewingHistory, setViewingHistory] = useState(false);
  const [historyMessages, setHistoryMessages] = useState<ChatMessage[]>([]);
  const [historyThreadId, setHistoryThreadId] = useState<string | undefined>();

  const handleNewChat = useCallback(() => {
    reset();
    setViewingHistory(false);
    setHistoryMessages([]);
    setHistoryThreadId(undefined);
  }, [reset]);

  const displayMessages = viewingHistory ? historyMessages : messages;

  return (
    <div className="flex h-screen overflow-hidden bg-[#111114] font-sans">
      {/* Sidebar */}
      {sidebarOpen && (
        <Sidebar
          threads={threads}
          activeThreadId={viewingHistory ? historyThreadId : threadId}
          onNewChat={handleNewChat}
          onSelectThread={handleSelectThread}
        />
      )}

      {/* Main chat area */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center gap-3 border-b border-white/5 px-4 py-3">
          <button
            id="toggle-sidebar-btn"
            onClick={() => setSidebarOpen((p) => !p)}
            className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-white/8 text-white/50 hover:text-white transition-colors"
          >
            {sidebarOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
          <span className="text-sm font-medium text-white/60 truncate">
            {viewingHistory
              ? threads.find((t) => t.thread_id === historyThreadId)?.title ?? "Thread"
              : threadId
              ? "Current conversation"
              : "New conversation"}
          </span>
          {viewingHistory && (
            <button
              onClick={handleNewChat}
              className="ml-auto text-xs text-violet-400 hover:text-violet-300 transition-colors"
            >
              Back to new chat
            </button>
          )}
        </header>

        {/* Error banner */}
        {error && (
          <div className="flex items-center gap-2 bg-red-950/50 border-b border-red-500/20 px-4 py-2.5">
            <AlertCircle size={14} className="text-red-400 flex-shrink-0" />
            <span className="text-xs text-red-300">{error}</span>
          </div>
        )}

        {/* Chat window */}
        <ChatWindow
          messages={displayMessages}
          isLoading={isLoading && !viewingHistory}
          onExampleClick={(t) => {
            if (viewingHistory) handleNewChat();
            handleSend(t);
          }}
        />

        {/* Input — disabled when viewing history */}
        {!viewingHistory && (
          <ChatInput onSend={handleSend} isLoading={isLoading} />
        )}
        {viewingHistory && (
          <div className="border-t border-white/5 bg-[#0d0d0f] px-4 py-4 text-center">
            <button
              onClick={handleNewChat}
              className="text-sm text-violet-400 hover:text-violet-300 transition-colors"
            >
              ← Start a new conversation
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
