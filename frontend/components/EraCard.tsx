import type { Era } from "@/lib/api";

export default function EraCard({ era, index }: { era: Era; index: number }) {
  const start = era.start_date.slice(0, 7);
  const end = era.end_date.slice(0, 7);

  return (
    <div className="border border-neutral-800/80 rounded-xl p-6 bg-neutral-900/20 hover:border-neutral-700 transition-colors">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <span className="text-xs font-mono text-neutral-600 uppercase tracking-widest">
            Era {index + 1}
          </span>
          <h3 className="text-lg font-semibold text-white mt-1">{era.title}</h3>
        </div>
        <span className="text-xs font-mono text-neutral-600 shrink-0 mt-1">
          {start} → {end}
        </span>
      </div>

      {era.key_events.length > 0 && (
        <ul className="space-y-1.5 mb-4">
          {era.key_events.map((event, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-neutral-500">
              <span className="text-neutral-700 mt-0.5 shrink-0">–</span>
              {event}
            </li>
          ))}
        </ul>
      )}

      <p className="text-neutral-500 text-sm leading-relaxed">{era.narrative}</p>

      <div className="mt-4 pt-4 border-t border-neutral-800/60 flex items-center justify-between">
        <span className="text-xs font-mono text-neutral-700">
          {era.commit_count.toLocaleString()} commits
        </span>
        {era.dominant_contributors.length > 0 && (
          <span className="text-xs font-mono text-neutral-700">
            {era.dominant_contributors.slice(0, 2).join(", ")}
          </span>
        )}
      </div>
    </div>
  );
}
