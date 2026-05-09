import type { RepoReport } from "@/lib/api";
import StatsBar from "./StatsBar";

export default function ReportHero({ report }: { report: RepoReport }) {
  const bornYear = report.first_commit.slice(0, 4);
  const lastYear = report.latest_commit.slice(0, 4);
  const yearsActive =
    bornYear === lastYear ? bornYear : `${bornYear} – ${lastYear}`;

  const stats = [
    { value: report.total_commits.toLocaleString(), label: "Commits" },
    { value: report.total_contributors, label: "Contributors" },
    { value: report.eras.length, label: "Eras" },
    { value: yearsActive, label: "Active" },
  ];

  return (
    <div className="mb-16">
      <p className="text-xs font-mono text-neutral-600 uppercase tracking-[0.3em] mb-4">
        Code Archeologist
      </p>
      <h1 className="text-5xl sm:text-6xl font-bold text-white tracking-tight leading-tight mb-2">
        {report.repo_name}
      </h1>
      {report.repo_url && (
        <a
          href={report.repo_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-neutral-600 font-mono text-sm hover:text-neutral-400 transition-colors"
        >
          {report.repo_url}
        </a>
      )}
      <div className="mt-8">
        <StatsBar stats={stats} />
      </div>
      <p className="mt-4 text-xs font-mono text-neutral-700">
        Analyzed {report.analysis_date.slice(0, 10)}
      </p>
    </div>
  );
}
