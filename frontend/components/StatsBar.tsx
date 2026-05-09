interface Stat {
  value: string | number;
  label: string;
}

export default function StatsBar({ stats }: { stats: Stat[] }) {
  return (
    <div className="flex flex-wrap gap-8 py-6 border-t border-b border-neutral-900">
      {stats.map((s) => (
        <div key={s.label}>
          <div className="text-2xl font-bold text-white font-mono">{s.value}</div>
          <div className="text-xs text-neutral-600 uppercase tracking-widest mt-0.5">
            {s.label}
          </div>
        </div>
      ))}
    </div>
  );
}
