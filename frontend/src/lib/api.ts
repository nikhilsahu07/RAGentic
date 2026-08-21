import axios from "axios";
import type { ChatResponse, ThreadDetail, ThreadSummary } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 60000, // 60s — LLM generation can take time
});

// Chat

export async function sendMessage(
  message: string,
  threadId?: string
): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/api/chat", {
    message,
    thread_id: threadId ?? null,
  });
  return data;
}

// Threads

export async function fetchThreads(): Promise<ThreadSummary[]> {
  const { data } = await api.get<ThreadSummary[]>("/api/threads");
  return data;
}

export async function fetchThread(threadId: string): Promise<ThreadDetail> {
  const { data } = await api.get<ThreadDetail>(`/api/threads/${threadId}`);
  return data;
}

// Documents

export async function ingestDocument(file: File) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/api/documents/ingest", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
