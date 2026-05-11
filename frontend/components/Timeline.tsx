"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { motion } from "framer-motion";
import type { Era } from "@/lib/api";

const ERA_COLORS = [
  "#2a2a2a",
  "#333",
  "#3d3d3d",
  "#474747",
  "#525252",
  "#5e5e5e",
  "#6a6a6a",
];

interface TooltipProps {
  active?: boolean;
  payload?: { payload: { title: string; commits: number; density: number; range: string } }[];
}

function CustomTooltip({ active, payload }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-[#111] border border-neutral-800 rounded-lg px-4 py-3 text-xs font-mono shadow-2xl">
      <p className="text-white font-semibold mb-1.5">{d.title}</p>
      <p className="text-neutral-500 mb-1">{d.range}</p>
      <p className="text-neutral-400">
        {d.commits.toLocaleString()} commits &middot;{" "}
        <span className="text-neutral-300">{d.density}/day</span>
      </p>
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

  const maxDensity = Math.max(...data.map((d) => d.density), 1);

  function CustomBar(props: Record<string, number>) {
    const { x, y, width, height, density } = props;
    const lightness = Math.round(18 + (density / maxDensity) * 52);
    return (
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={`oklch(${lightness}% 0 0)`}
        rx={3}
        ry={3}
      />
    );
  }
  const totalMs =
    new Date(eras.at(-1)!.end_date).getTime() -
    new Date(eras[0].start_date).getTime();

  return (
    <div className="w-full">
      <p className="text-xs font-mono text-neutral-700 uppercase tracking-widest mb-5">
        Commit density · commits per day
      </p>

      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={data} barCategoryGap="18%">
          <XAxis
            dataKey="title"
            tick={{ fill: "#404040", fontSize: 10, fontFamily: "var(--font-geist-mono)" }}
            axisLine={false}
            tickLine={false}
            interval={0}
            height={40}
          />
          <YAxis hide />
          <Tooltip
            content={<CustomTooltip />}
            cursor={{ fill: "rgba(255,255,255,0.02)" }}
          />
          <Bar dataKey="density" radius={[3, 3, 0, 0]}>
            {data.map((d, i) => {
              const intensity = d.density / maxDensity;
              const lightness = Math.round(18 + intensity * 52);
              return (
                <Cell
                  key={i}
                  fill={`oklch(${lightness}% 0 0)`}
                />
              );
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Era strip */}
      <div className="mt-4 flex rounded overflow-hidden h-1.5 gap-px">
        {eras.map((era, i) => {
          const startMs = new Date(era.start_date).getTime();
          const endMs = new Date(era.end_date).getTime();
          const width = ((endMs - startMs) / totalMs) * 100;
          return (
            <motion.div
              key={i}
              title={era.title}
              initial={{ scaleX: 0, originX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 0.6, delay: i * 0.08, ease: "easeOut" }}
              style={{
                width: `${width}%`,
                backgroundColor: ERA_COLORS[i % ERA_COLORS.length],
              }}
              className="h-full"
            />
          );
        })}
      </div>

      {/* Era labels under strip */}
      <div className="flex mt-2.5 gap-px" style={{ fontSize: 0 }}>
        {eras.map((era, i) => {
          const startMs = new Date(era.start_date).getTime();
          const endMs = new Date(era.end_date).getTime();
          const width = ((endMs - startMs) / totalMs) * 100;
          return (
            <div
              key={i}
              style={{ width: `${width}%` }}
              className="overflow-hidden"
            >
              <span className="text-[10px] font-mono text-neutral-700 whitespace-nowrap">
                {era.start_date.slice(0, 7)}
              </span>
            </div>
          );
        })}
      </div>
      <div className="flex justify-end mt-0.5">
        <span className="text-[10px] font-mono text-neutral-700">
          {eras.at(-1)?.end_date.slice(0, 7)}
        </span>
      </div>
    </div>
  );
}
