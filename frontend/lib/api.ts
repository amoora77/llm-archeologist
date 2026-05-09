export interface Era {
  title: string;
  start_date: string;
  end_date: string;
  commit_count: number;
  dominant_contributors: string[];
  key_events: string[];
  narrative: string;
}

export interface Contributor {
  name: string;
  email: string;
  commit_count: number;
  first_commit: string;
  last_commit: string;
  primary_areas: string[];
  signature_files: string[];
  profile: string;
}

export interface Pivot {
  date: string;
  title: string;
  description: string;
  evidence: string[];
  category: string;
  significance: string;
}

export interface GhostSystem {
  name: string;
  existed_from: string;
  deleted_on: string;
  files: string[];
  description: string;
}

export interface DarkPeriod {
  week: string;
  commit_count: number;
  rolling_avg: number;
  intensity_ratio: number;
  late_night_commits: number;
  start_date: string;
  end_date: string;
  contributors: string[];
}

export interface RepoReport {
  repo_url: string;
  repo_name: string;
  analysis_date: string;
  total_commits: number;
  total_contributors: number;
  first_commit: string;
  latest_commit: string;
  origin_story: string;
  eras: Era[];
  contributors: Contributor[];
  pivots: Pivot[];
  ghost_systems: GhostSystem[];
  dark_periods: DarkPeriod[];
  present_state: string;
  archeologists_note: string;
  top_churned_files: string[];
}

const backendUrl =
  typeof window === "undefined"
    ? (process.env.BACKEND_URL ?? "http://localhost:8000")
    : "";

export async function fetchReport(reportId: string): Promise<RepoReport> {
  const res = await fetch(`${backendUrl}/api/report/${reportId}`, {
    cache: "force-cache",
  });
  if (!res.ok) throw new Error("Report not found");
  return res.json();
}
