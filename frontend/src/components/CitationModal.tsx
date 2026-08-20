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
      <div className="relative flex h-[88vh] w-full max-w-5xl flex-col rounded-2xl border border-white/10 bg-[#111114] shadow-2xl overflow-hidden">
        {/* Modal header */}
        <div className="flex items-center gap-3 border-b border-white/8 px-6 py-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/20 border border-violet-500/30">
            <FileText size={15} className="text-violet-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white truncate">{citation.doc_name}</p>
            <p className="text-xs text-white/40">Page {citation.page_num} · Source [{citation.index}]</p>
          </div>
          <div className="flex items-center gap-2">
            {citation.presigned_url && (
              <a
                href={citation.presigned_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-lg bg-white/5 hover:bg-white/10 px-3 py-1.5 text-xs text-white/60 hover:text-white transition-colors"
              >
                <ExternalLink size={12} />
                Open
              </a>
            )}
            <button
              id="citation-modal-close"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-white/10 text-white/50 hover:text-white transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Retrieved chunk — the evidence */}
        <div className="border-b border-white/8 bg-violet-950/20 px-6 py-4">
          <p className="text-xs font-medium text-violet-400 mb-2 uppercase tracking-wider">Retrieved Context</p>
          <blockquote className="text-sm text-white/75 leading-relaxed line-clamp-4 italic border-l-2 border-violet-500/50 pl-4">
            {citation.chunk_text}
          </blockquote>
        </div>

        {/* PDF viewer */}
        <div className="flex-1 bg-[#0a0a0c]">
          {citation.presigned_url ? (
            <iframe
              src={citation.presigned_url}
              className="h-full w-full"
              title={`${citation.doc_name} — page ${citation.page_num}`}
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <FileText size={40} className="mx-auto text-white/15 mb-3" />
                <p className="text-sm text-white/30">PDF preview unavailable</p>
                <p className="text-xs text-white/20 mt-1">The document URL has expired or is unavailable</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
