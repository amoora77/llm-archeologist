"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { Era } from "@/lib/api";

interface TooltipPayload {
  payload?: { title: string; commits: number; range: string };
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayload[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  if (!d) return null;
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-3 text-xs font-mono shadow-xl">
      <p className="text-white font-semibold mb-1">{d.title}</p>
      <p className="text-neutral-500">{d.range}</p>
      <p className="text-neutral-400 mt-1">{d.commits.toLocaleString()} commits</p>
    </div>
  );
}

export default function Timeline({ eras }: { eras: Era[] }) {
  const data = eras.map((era) => {
    const startMs = new Date(era.start_date).getTime();
    const endMs = new Date(era.end_date).getTime();
    const days = Math.max(1, (endMs - startMs) / 86_400_000);
    return {
      title: era.title,
      commits: era.commit_count,
      density: parseFloat((era.commit_count / days).toFixed(2)),
      range: `${era.start_date.slice(0, 7)} → ${era.end_date.slice(0, 7)}`,
    };
  });

  return (
    <div className="w-full">
      {/* Commit density bar chart */}
      <p className="text-xs font-mono text-neutral-600 uppercase tracking-widest mb-4">
        Commit density (commits / day)
      </p>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={data} barCategoryGap="20%">
          <XAxis
            dataKey="title"
            tick={{ fill: "#525252", fontSize: 11, fontFamily: "var(--font-geist-mono)" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis hide />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
          <Bar dataKey="density" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => (
              <Cell
                key={i}
                fill={i === data.length - 1 ? "#d4d4d4" : "#3a3a3a"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Era strip */}
      <div className="mt-6 flex rounded-lg overflow-hidden h-2 gap-px">
        {eras.map((era, i) => {
          const startMs = new Date(era.start_date).getTime();
          const endMs = new Date(era.end_date).getTime();
          const totalMs =
            new Date(eras.at(-1)!.end_date).getTime() -
            new Date(eras[0].start_date).getTime();
          const width = ((endMs - startMs) / totalMs) * 100;
          const lightness = 20 + (i / Math.max(eras.length - 1, 1)) * 45;
          return (
            <div
              key={i}
              title={era.title}
              style={{ width: `${width}%`, backgroundColor: `oklch(${lightness}% 0 0)` }}
              className="h-full"
            />
          );
        })}
      </div>
      <div className="flex justify-between mt-2">
        <span className="text-xs font-mono text-neutral-700">
          {eras[0]?.start_date.slice(0, 7)}
        </span>
        <span className="text-xs font-mono text-neutral-700">
          {eras.at(-1)?.end_date.slice(0, 7)}
        </span>
      </div>
    </div>
  );
}
