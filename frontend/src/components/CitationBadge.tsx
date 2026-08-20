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
            className="flex items-center gap-1.5 rounded-full border border-violet-500/30 bg-violet-500/10 hover:bg-violet-500/20 px-2.5 py-1 text-xs text-violet-300 hover:text-violet-200 transition-all duration-150 hover:border-violet-400/50"
          >
            <span className="font-semibold">[{c.index}]</span>
            <span className="text-violet-400/70 truncate max-w-[140px]">{c.doc_name}</span>
            <span className="text-violet-500/60">p.{c.page_num}</span>
          </button>
        ))}
      </div>

      {open && <CitationModal citation={open} onClose={() => setOpen(null)} />}
    </>
  );
}
