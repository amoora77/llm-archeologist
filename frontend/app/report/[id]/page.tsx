import { notFound } from "next/navigation";
import { fetchReport } from "@/lib/api";
import type { Pivot, DarkPeriod } from "@/lib/api";
import ReportHero from "@/components/ReportHero";
import NarrativeBlock from "@/components/NarrativeBlock";
import EraCard from "@/components/EraCard";
import Timeline from "@/components/Timeline";
import ContributorProfile from "@/components/ContributorProfile";
import GhostCodeSection from "@/components/GhostCodeSection";

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
    <h2 className="text-xs font-mono text-neutral-600 uppercase tracking-[0.3em] mb-8 mt-20 first:mt-0">
      {children}
    </h2>
  );
}

function PivotCard({ pivot }: { pivot: Pivot }) {
  return (
    <div className="border border-neutral-800/80 rounded-xl p-6 bg-neutral-900/20 hover:border-neutral-700 transition-colors">
      <div className="flex items-center gap-3 mb-3">
        <span className="text-xs font-mono text-neutral-600 border border-neutral-800 rounded px-2 py-0.5">
          {CATEGORY_LABELS[pivot.category] ?? pivot.category}
        </span>
        {pivot.significance === "high" && (
          <span className="text-xs font-mono text-amber-600/80">high significance</span>
        )}
      </div>
      <h3 className="text-white font-semibold mb-1">{pivot.title}</h3>
      <p className="text-xs font-mono text-neutral-600 mb-3">{pivot.date.slice(0, 10)}</p>
      <p className="text-neutral-400 text-sm leading-relaxed">{pivot.description}</p>
    </div>
  );
}

function DarkPeriodRow({ period }: { period: DarkPeriod }) {
  return (
    <div className="flex items-start gap-6 py-4 border-b border-neutral-900 last:border-0">
      <span className="text-xs font-mono text-neutral-600 shrink-0 mt-0.5 w-24">
        {period.week}
      </span>
      <div className="min-w-0">
        <p className="text-sm text-neutral-400">
          <span className="text-white font-semibold">{period.commit_count}</span> commits —{" "}
          <span className="text-amber-500/80">{period.intensity_ratio}×</span> above normal
          {period.late_night_commits > 0 && (
            <span className="text-neutral-600">
              {" "}
              · {period.late_night_commits} late-night
            </span>
          )}
        </p>
        <p className="text-xs font-mono text-neutral-700 mt-1">
          {period.contributors.join(", ")}
        </p>
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

  return (
    <main className="max-w-[860px] mx-auto px-6 py-20">
      <ReportHero report={report} />

      <SectionLabel>Origin Story</SectionLabel>
      <NarrativeBlock text={report.origin_story} />

      {report.eras.length > 0 && (
        <>
          <SectionLabel>The Eras</SectionLabel>
          <div className="mb-10">
            <Timeline eras={report.eras} />
          </div>
          <div className="grid grid-cols-1 gap-4">
            {report.eras.map((era, i) => (
              <EraCard key={i} era={era} index={i} />
            ))}
          </div>
        </>
      )}

      {report.pivots.length > 0 && (
        <>
          <SectionLabel>The Pivots</SectionLabel>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {report.pivots.map((pivot, i) => (
              <PivotCard key={i} pivot={pivot} />
            ))}
          </div>
        </>
      )}

      {report.contributors.length > 0 && (
        <>
          <SectionLabel>The Characters</SectionLabel>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {report.contributors.map((c, i) => (
              <ContributorProfile key={i} contributor={c} />
            ))}
          </div>
        </>
      )}

      {report.ghost_systems.length > 0 && (
        <>
          <SectionLabel>Ghost Code</SectionLabel>
          <div className="grid grid-cols-1 gap-4">
            {report.ghost_systems.map((g, i) => (
              <GhostCodeSection key={i} ghost={g} />
            ))}
          </div>
        </>
      )}

      {report.dark_periods.length > 0 && (
        <>
          <SectionLabel>Dark Periods</SectionLabel>
          <div>
            {report.dark_periods.map((dp, i) => (
              <DarkPeriodRow key={i} period={dp} />
            ))}
          </div>
        </>
      )}

      <SectionLabel>Present State</SectionLabel>
      <NarrativeBlock text={report.present_state} />

      {report.archeologists_note && (
        <>
          <SectionLabel>The Archeologist&apos;s Note</SectionLabel>
          <blockquote className="border-l-2 border-neutral-700 pl-6 py-1">
            <NarrativeBlock text={report.archeologists_note} />
          </blockquote>
        </>
      )}

      <div className="mt-20 pt-8 border-t border-neutral-900 flex items-center justify-between">
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
    </main>
  );
}
