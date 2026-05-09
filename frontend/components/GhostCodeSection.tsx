import type { GhostSystem } from "@/lib/api";

export default function GhostCodeSection({ ghost }: { ghost: GhostSystem }) {
  const start = ghost.existed_from.slice(0, 7);
  const end = ghost.deleted_on.slice(0, 7);
  const lifespanDays = Math.round(
    (new Date(ghost.deleted_on).getTime() - new Date(ghost.existed_from).getTime()) /
      86_400_000
  );

  return (
    <div className="border border-neutral-800/50 rounded-xl p-6 bg-neutral-950/60 hover:border-neutral-700/60 transition-colors">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div>
          <span className="text-xs font-mono text-neutral-700 uppercase tracking-widest">
            Deleted system
          </span>
          <h3 className="text-neutral-300 font-semibold mt-1 font-mono">{ghost.name}/</h3>
        </div>
        <div className="text-right shrink-0">
          <p className="text-xs font-mono text-neutral-700">
            {start} – {end}
          </p>
          <p className="text-xs font-mono text-neutral-700 mt-0.5">
            {lifespanDays} days
          </p>
        </div>
      </div>

      <p className="text-neutral-500 text-sm leading-relaxed">{ghost.description}</p>

      {ghost.files.length > 0 && (
        <div className="mt-4 pt-4 border-t border-neutral-900">
          <p className="text-xs font-mono text-neutral-700 mb-2">Files</p>
          <div className="flex flex-wrap gap-2">
            {ghost.files.slice(0, 6).map((f) => (
              <span key={f} className="text-xs font-mono text-neutral-700 truncate max-w-[200px]">
                {f}
              </span>
            ))}
            {ghost.files.length > 6 && (
              <span className="text-xs font-mono text-neutral-700">
                +{ghost.files.length - 6} more
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
