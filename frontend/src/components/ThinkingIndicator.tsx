"use client";

export function ThinkingIndicator() {
  return (
    <div className="flex items-start gap-3 px-4 py-3">
      {/* Avatar */}
      <div className="h-7 w-7 flex-shrink-0 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center mt-0.5">
        <span className="text-[10px] font-bold text-white">R</span>
      </div>

      {/* Animated dots */}
      <div className="flex items-center gap-1.5 rounded-2xl bg-white/5 border border-white/8 px-4 py-3">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-bounce"
            style={{ animationDelay: `${i * 0.15}s`, animationDuration: "0.9s" }}
          />
        ))}
      </div>
    </div>
  );
}
