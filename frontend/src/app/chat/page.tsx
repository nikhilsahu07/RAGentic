"use client";

import { useCallback, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { ChatWindow } from "@/components/ChatWindow";
import { ChatInput } from "@/components/ChatInput";
import { useChat } from "@/hooks/useChat";
import { useThreads } from "@/hooks/useThreads";
import { fetchThread } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";
import { AlertCircle, PanelLeftClose, PanelLeft } from "lucide-react";

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
  const activeThreadMeta = viewingHistory
    ? threads.find((t) => t.thread_id === historyThreadId)
    : threads.find((t) => t.thread_id === threadId);

  const msgCount = viewingHistory ? historyMessages.length : messages.length;

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg)] font-sans">
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
        <header className="flex items-center gap-3 border-b border-[var(--border)] px-4 py-3">
          <button
            id="toggle-sidebar-btn"
            onClick={() => setSidebarOpen((p) => !p)}
            aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-transparent hover:border-[var(--border)] hover:bg-[var(--surface)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors duration-150"
          >
            {sidebarOpen ? <PanelLeftClose size={15} /> : <PanelLeft size={15} />}
          </button>

          <div className="flex items-baseline gap-2 min-w-0">
            <span className="text-sm font-medium text-[var(--text-primary)] truncate">
              {viewingHistory
                ? activeThreadMeta?.title ?? "Thread"
                : threadId
                  ? activeThreadMeta?.title ?? "Current conversation"
                  : "New conversation"}
            </span>
            {msgCount > 0 && (
              <span className="font-mono-ui text-[10px] text-[var(--text-tertiary)] whitespace-nowrap">
                {msgCount} msg{msgCount !== 1 ? "s" : ""}
              </span>
            )}
          </div>

          {viewingHistory && (
            <button
              onClick={handleNewChat}
              className="ml-auto text-xs text-[var(--accent-text)] hover:text-[var(--accent-hover)] transition-colors"
            >
              Back to new chat
            </button>
          )}
        </header>

        {/* Error banner */}
        {error && (
          <div className="flex items-center gap-2 bg-[var(--red-soft)] border-b border-[var(--red-soft-border)] px-4 py-2.5">
            <AlertCircle size={14} className="text-[var(--red)] flex-shrink-0" />
            <span className="text-xs text-[var(--red)]">{error}</span>
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
          <div className="border-t border-[var(--border)] bg-[var(--surface)] px-4 py-4 text-center">
            <button
              onClick={handleNewChat}
              className="text-sm text-[var(--accent-text)] hover:text-[var(--accent-hover)] transition-colors"
            >
              ← Start a new conversation
            </button>
          </div>
        )}
      </div>
    </div>
  );
}