import type { Contributor } from "@/lib/api";

export default function ContributorProfile({ contributor }: { contributor: Contributor }) {
  const start = contributor.first_commit.slice(0, 7);
  const end = contributor.last_commit.slice(0, 7);
  const initials = contributor.name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="border border-neutral-800/80 rounded-xl p-6 bg-neutral-900/20 hover:border-neutral-700 transition-colors">
      <div className="flex items-start gap-4 mb-4">
        <div className="w-10 h-10 rounded-full bg-neutral-800 flex items-center justify-center shrink-0">
          <span className="text-sm font-mono text-neutral-400">{initials}</span>
        </div>
        <div className="min-w-0">
          <h3 className="text-white font-semibold truncate">{contributor.name}</h3>
          <p className="text-xs font-mono text-neutral-600 mt-0.5">
            {contributor.commit_count.toLocaleString()} commits &middot; {start} – {end}
          </p>
        </div>
      </div>

      <p className="text-neutral-400 text-sm leading-relaxed mb-4">{contributor.profile}</p>

      {contributor.primary_areas.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {contributor.primary_areas.slice(0, 5).map((area) => (
            <span
              key={area}
              className="text-xs font-mono text-neutral-600 border border-neutral-800 rounded px-2 py-0.5"
            >
              {area}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
