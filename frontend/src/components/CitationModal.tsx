"use client";

import { X, FileText, ExternalLink } from "lucide-react";
import type { Citation } from "@/lib/types";
import { useEffect, useRef } from "react";

interface CitationModalProps {
  citation: Citation;
  onClose: () => void;
}

export function CitationModal({ citation, onClose }: CitationModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  // Close on backdrop click
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
    >
      <div className="relative flex h-[88vh] w-full max-w-5xl flex-col rounded-xl border border-[var(--border-hover)] bg-[var(--bg)] shadow-2xl overflow-hidden">
        {/* Modal header */}
        <div className="flex items-center gap-3 border-b border-[var(--border)] px-6 py-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-md border border-[var(--border-hover)] bg-[var(--surface)]">
            <FileText size={14} className="text-[var(--accent-text)]" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-[var(--text-primary)] truncate">
              {citation.doc_name}
            </p>
            <p className="font-mono-ui text-[11px] text-[var(--text-tertiary)]">
              page {citation.page_num} · source [{citation.index}]
            </p>
          </div>
          <div className="flex items-center gap-2">
            {citation.presigned_url && (
              <a
                href={citation.presigned_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] hover:border-[var(--border-hover)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              >
                <ExternalLink size={12} />
                Open
              </a>
            )}
            <button
              id="citation-modal-close"
              onClick={onClose}
              aria-label="Close"
              className="flex h-8 w-8 items-center justify-center rounded-md border border-transparent hover:border-[var(--border)] hover:bg-[var(--surface)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
            >
              <X size={15} />
            </button>
          </div>
        </div>

        {/* Retrieved chunk — the evidence */}
        <div className="border-b border-[var(--border)] bg-[var(--surface)] px-6 py-4">
          <p className="font-mono-ui text-[10px] font-medium text-[var(--accent-text)] mb-2 uppercase tracking-wider">
            Retrieved context
          </p>
          <blockquote className="text-sm text-[var(--text-secondary)] leading-relaxed line-clamp-4 border-l-2 border-[var(--border-hover)] pl-4">
            {citation.chunk_text}
          </blockquote>
        </div>

        {/* PDF viewer */}
        <div className="flex-1 bg-[#08080a]">
          {citation.presigned_url ? (
            <iframe
              src={citation.presigned_url}
              className="h-full w-full"
              title={`${citation.doc_name} — page ${citation.page_num}`}
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <FileText size={36} className="mx-auto text-[var(--text-tertiary)] mb-3" />
                <p className="text-sm text-[var(--text-secondary)]">PDF preview unavailable</p>
                <p className="text-xs text-[var(--text-tertiary)] mt-1">
                  The document URL has expired or is unavailable
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}