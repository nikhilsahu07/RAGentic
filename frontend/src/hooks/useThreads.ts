"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchThreads } from "@/lib/api";
import type { ThreadSummary } from "@/lib/types";

export function useThreads() {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchThreads();
      setThreads(data);
    } catch {
      // Silently fail — sidebar is non-critical
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { threads, isLoading, refresh };
}
