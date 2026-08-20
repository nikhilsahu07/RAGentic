"use client";

export function ThinkingIndicator() {
  return (
    <div className="flex items-start gap-3 px-4 py-3">
      {/* Avatar — matches the assistant mark used elsewhere */}
      <div className="h-7 w-7 flex-shrink-0 rounded-md border border-[var(--border-hover)] bg-[var(--surface)] flex items-center justify-center mt-0.5">
        <span className="font-mono-ui text-[10px] font-semibold text-[var(--accent-text)]">R</span>
      </div>

      {/* Quiet, pulsing dots — no bounce, no color noise */}
      <div className="flex items-center gap-1.5 rounded-lg rounded-tl-sm border border-[var(--border)] bg-[var(--surface)] px-4 py-3.5">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="h-1.5 w-1.5 rounded-full bg-[var(--text-tertiary)] animate-pulse"
            style={{ animationDelay: `${i * 0.2}s`, animationDuration: "1.2s" }}
          />
        ))}
      </div>
    </div>
  );
}