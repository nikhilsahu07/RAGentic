export interface Citation {
  index: number;
  doc_name: string;
  doc_id: string;
  s3_key: string;
  page_num: number;
  chunk_text: string;
  presigned_url: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: "direct" | "retrieve" | "tool" | "declined" | null;
  citations?: Citation[];
  timestamp: string;
}

export interface ChatResponse {
  thread_id: string;
  message_id: string;
  answer: string;
  intent: "direct" | "retrieve" | "tool" | "declined";
  citations: Citation[];
  latency_ms: number;
  token_count: number;
}

export interface ThreadSummary {
  thread_id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ThreadDetail {
  thread_id: string;
  title: string;
  messages: ChatMessage[];
}
