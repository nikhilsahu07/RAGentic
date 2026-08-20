"use client";

import { useState } from "react";
import type { Citation } from "@/lib/types";
import { CitationModal } from "./CitationModal";

interface CitationBadgeProps {
  citations: Citation[];
}

export function CitationBadge({ citations }: CitationBadgeProps) {
  const [open, setOpen] = useState<Citation | null>(null);

  if (!citations || citations.length === 0) return null;

  return (
    <>
      <div className="flex flex-wrap gap-1.5 mt-3">
        {citations.map((c) => (
          <button
            key={c.index}
            id={`citation-${c.doc_id.slice(0, 8)}-${c.index}`}
            onClick={() => setOpen(c)}
            title={`${c.doc_name} — page ${c.page_num}`}
            className="flex items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] hover:border-[var(--border-hover)] px-2.5 py-1 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors duration-150"
          >
            <span className="font-mono-ui text-[10px] text-[var(--accent-text)]">[{c.index}]</span>
            <span className="truncate max-w-[140px]">{c.doc_name}</span>
            <span className="font-mono-ui text-[10px] text-[var(--text-tertiary)]">p.{c.page_num}</span>
          </button>
        ))}
      </div>

      {open && <CitationModal citation={open} onClose={() => setOpen(null)} />}
    </>
  );
}