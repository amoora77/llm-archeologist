import { notFound } from "next/navigation";
import { fetchReport } from "@/lib/api";
import type { Pivot, DarkPeriod } from "@/lib/api";
import ReportHero from "@/components/ReportHero";
import NarrativeBlock from "@/components/NarrativeBlock";
import EraCard from "@/components/EraCard";
import Timeline from "@/components/Timeline";
import ContributorProfile from "@/components/ContributorProfile";
import GhostCodeSection from "@/components/GhostCodeSection";
import FadeIn from "@/components/FadeIn";

const CATEGORY_LABELS: Record<string, string> = {
  architecture_pivot: "Architecture Pivot",
  technology_migration: "Tech Migration",
  feature_expansion: "Feature Expansion",
  cleanup: "Cleanup",
  incident_response: "Incident Response",
  unknown: "Change",
};

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xs font-mono text-neutral-600 uppercase tracking-[0.3em] mb-8 mt-24">
      {children}
    </h2>
  );
}

function PivotCard({ pivot }: { pivot: Pivot }) {
  return (
    <div className="border border-neutral-800/80 rounded-xl p-5 sm:p-6 bg-neutral-900/20 hover:border-neutral-700 transition-colors h-full">
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="text-xs font-mono text-neutral-600 border border-neutral-800 rounded px-2 py-0.5 shrink-0">
          {CATEGORY_LABELS[pivot.category] ?? pivot.category}
        </span>
        {pivot.significance === "high" && (
          <span className="text-xs font-mono text-amber-600/80">high significance</span>
        )}
      </div>
      <h3 className="text-white font-semibold mb-1 leading-snug">{pivot.title}</h3>
      <p className="text-xs font-mono text-neutral-700 mb-3">{pivot.date.slice(0, 10)}</p>
      <p className="text-neutral-500 text-sm leading-relaxed">{pivot.description}</p>
    </div>
  );
}

function DarkPeriodCard({ period, maxIntensity }: { period: DarkPeriod; maxIntensity: number }) {
  const intensity = period.intensity_ratio / maxIntensity;
  const barWidth = Math.round(intensity * 100);

  return (
    <div className="border border-neutral-800/60 rounded-xl p-5 bg-neutral-900/10 hover:border-neutral-700/60 transition-colors">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div>
          <p className="text-xs font-mono text-neutral-600 mb-1">{period.week}</p>
          <p className="text-white font-semibold text-sm">
            {period.commit_count.toLocaleString()} commits
          </p>
        </div>
        <div className="text-right shrink-0">
          <span className="text-lg font-bold font-mono text-amber-500/90">
            {period.intensity_ratio}×
          </span>
          <p className="text-xs font-mono text-neutral-700">above normal</p>
        </div>
      </div>

      {/* Intensity bar */}
      <div className="h-px bg-neutral-900 rounded-full mb-3 overflow-hidden">
        <div
          className="h-full bg-amber-600/50 rounded-full transition-all"
          style={{ width: `${barWidth}%` }}
        />
      </div>

      <div className="flex items-center justify-between gap-4">
        <p className="text-xs font-mono text-neutral-700 truncate">
          {period.contributors.slice(0, 3).join(", ")}
          {period.contributors.length > 3 && ` +${period.contributors.length - 3}`}
        </p>
        {period.late_night_commits > 0 && (
          <span className="text-xs font-mono text-neutral-600 shrink-0">
            🌙 {period.late_night_commits} late-night
          </span>
        )}
      </div>
    </div>
  );
}

export default async function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let report;
  try {
    report = await fetchReport(id);
  } catch {
    notFound();
  }

  const maxIntensity = report.dark_periods.length
    ? Math.max(...report.dark_periods.map((dp) => dp.intensity_ratio))
    : 1;

  return (
    <main className="max-w-[860px] mx-auto px-4 sm:px-6 py-16 sm:py-20">
      <FadeIn>
        <ReportHero report={report} />
      </FadeIn>

      <FadeIn>
        <SectionLabel>Origin Story</SectionLabel>
        <NarrativeBlock text={report.origin_story} />
      </FadeIn>

      {report.eras.length > 0 && (
        <FadeIn>
          <SectionLabel>The Eras</SectionLabel>
          <div className="mb-10">
            <Timeline eras={report.eras} />
          </div>
          <div className="grid grid-cols-1 gap-4">
            {report.eras.map((era, i) => (
              <FadeIn key={i} delay={i * 0.05}>
                <EraCard era={era} index={i} />
              </FadeIn>
            ))}
          </div>
        </FadeIn>
      )}

      {report.pivots.length > 0 && (
        <FadeIn>
          <SectionLabel>The Pivots</SectionLabel>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {report.pivots.map((pivot, i) => (
              <FadeIn key={i} delay={i * 0.05}>
                <PivotCard pivot={pivot} />
              </FadeIn>
            ))}
          </div>
        </FadeIn>
      )}

      {report.contributors.length > 0 && (
        <FadeIn>
          <SectionLabel>The Characters</SectionLabel>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {report.contributors.map((c, i) => (
              <FadeIn key={i} delay={i * 0.05}>
                <ContributorProfile contributor={c} />
              </FadeIn>
            ))}
          </div>
        </FadeIn>
      )}

      {report.ghost_systems.length > 0 && (
        <FadeIn>
          <SectionLabel>Ghost Code</SectionLabel>
          <div className="grid grid-cols-1 gap-4">
            {report.ghost_systems.map((g, i) => (
              <FadeIn key={i} delay={i * 0.05}>
                <GhostCodeSection ghost={g} />
              </FadeIn>
            ))}
          </div>
        </FadeIn>
      )}

      {report.dark_periods.length > 0 && (
        <FadeIn>
          <SectionLabel>Dark Periods</SectionLabel>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {report.dark_periods.map((dp, i) => (
              <FadeIn key={i} delay={i * 0.04}>
                <DarkPeriodCard period={dp} maxIntensity={maxIntensity} />
              </FadeIn>
            ))}
          </div>
        </FadeIn>
      )}

      <FadeIn>
        <SectionLabel>Present State</SectionLabel>
        <NarrativeBlock text={report.present_state} />
      </FadeIn>

      {report.archeologists_note && (
        <FadeIn>
          <SectionLabel>The Archeologist&apos;s Note</SectionLabel>
          <blockquote className="border-l-2 border-neutral-800 pl-6 py-1">
            <NarrativeBlock text={report.archeologists_note} />
          </blockquote>
        </FadeIn>
      )}

      <FadeIn>
        <div className="mt-24 pt-8 border-t border-neutral-900 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <a
            href="/"
            className="text-xs font-mono text-neutral-700 hover:text-neutral-400 transition-colors"
          >
            ← Analyze another repo
          </a>
          <a
            href={`/api/report/${id}/html`}
            target="_blank"
            className="text-xs font-mono text-neutral-700 hover:text-neutral-400 transition-colors"
          >
            Export HTML →
          </a>
        </div>
      </FadeIn>
    </main>
  );
}
