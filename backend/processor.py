from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from models import Commit, ContributorStats, GhostSystem


def detect_eras(commits: list[Commit]) -> list[tuple[datetime, datetime]]:
    if not commits:
        return []

    # bucket commits by ISO week
    week_counts: dict[str, int] = defaultdict(int)
    week_authors: dict[str, set[str]] = defaultdict(set)
    for c in commits:
        week = c.timestamp.strftime("%Y-%W")
        week_counts[week] += 1
        week_authors[week].add(c.author_email)

    weeks = sorted(week_counts.keys())
    if len(weeks) < 3:
        return [(commits[0].timestamp, commits[-1].timestamp)]

    # rolling 3-week average to detect frequency shifts
    era_boundaries: list[datetime] = [commits[0].timestamp]
    for i in range(3, len(weeks)):
        prev_avg = sum(week_counts[weeks[j]] for j in range(i - 3, i)) / 3
        curr = week_counts[weeks[i]]
        if prev_avg > 0 and (curr / prev_avg > 1.5 or curr / prev_avg < 0.5):
            # find the first commit in this week
            week_label = weeks[i]
            for c in commits:
                if c.timestamp.strftime("%Y-%W") == week_label:
                    era_boundaries.append(c.timestamp)
                    break

    era_boundaries.append(commits[-1].timestamp)

    # deduplicate boundaries that are too close (< 30 days apart)
    merged: list[datetime] = [era_boundaries[0]]
    for b in era_boundaries[1:]:
        if (b - merged[-1]).days >= 30:
            merged.append(b)
    if merged[-1] != era_boundaries[-1]:
        merged.append(era_boundaries[-1])

    # cap at 7 eras
    if len(merged) > 8:
        step = len(merged) // 7
        merged = [merged[0]] + merged[1:-1:step][:6] + [merged[-1]]

    eras = [(merged[i], merged[i + 1]) for i in range(len(merged) - 1)]
    return eras


def compute_contributor_stats(commits: list[Commit]) -> dict[str, ContributorStats]:
    stats: dict[str, ContributorStats] = {}

    for c in commits:
        key = c.author_email
        if key not in stats:
            stats[key] = ContributorStats(
                name=c.author_name,
                email=c.author_email,
                commit_count=0,
                first_commit=c.timestamp,
                last_commit=c.timestamp,
            )

        s = stats[key]
        s.commit_count += 1
        s.first_commit = min(s.first_commit, c.timestamp)
        s.last_commit = max(s.last_commit, c.timestamp)

        for f in c.files_changed:
            s.files_touched.add(f)
            s.file_commit_counts[f] = s.file_commit_counts.get(f, 0) + 1
            top_dir = f.split("/")[0] if "/" in f else "."
            s.dir_counts[top_dir] = s.dir_counts.get(top_dir, 0) + 1

        total_change = c.insertions + c.deletions
        if total_change > 200:
            s.notable_commits.append(c)
            s.notable_commits.sort(key=lambda x: x.insertions + x.deletions, reverse=True)
            s.notable_commits = s.notable_commits[:10]

    return stats


def compute_file_churn(commits: list[Commit]) -> dict[str, int]:
    churn: dict[str, int] = defaultdict(int)
    for c in commits:
        for f in c.files_changed:
            churn[f] += 1
    return dict(sorted(churn.items(), key=lambda x: x[1], reverse=True))


def detect_dark_periods(commits: list[Commit]) -> list[dict]:
    if not commits:
        return []

    week_commits: dict[str, list[Commit]] = defaultdict(list)
    for c in commits:
        week = c.timestamp.strftime("%Y-%W")
        week_commits[week].append(c)

    weeks = sorted(week_commits.keys())
    window = 4
    dark_periods = []

    for i in range(window, len(weeks)):
        rolling_avg = sum(len(week_commits[weeks[j]]) for j in range(i - window, i)) / window
        current_week_commits = week_commits[weeks[i]]
        current_count = len(current_week_commits)

        if rolling_avg > 0 and current_count / rolling_avg >= 3:
            late_night = sum(
                1 for c in current_week_commits
                if c.timestamp.hour >= 22 or c.timestamp.hour <= 4
            )
            dark_periods.append({
                "week": weeks[i],
                "commit_count": current_count,
                "rolling_avg": round(rolling_avg, 1),
                "intensity_ratio": round(current_count / rolling_avg, 1),
                "late_night_commits": late_night,
                "start_date": min(c.timestamp for c in current_week_commits),
                "end_date": max(c.timestamp for c in current_week_commits),
                "contributors": list({c.author_name for c in current_week_commits}),
            })

    return dark_periods


def identify_ghost_systems(commits: list[Commit]) -> list[GhostSystem]:
    # track which directories are alive at any given commit
    dir_first_seen: dict[str, datetime] = {}
    dir_last_seen: dict[str, datetime] = {}
    dir_commits: dict[str, int] = defaultdict(int)
    dir_files: dict[str, set[str]] = defaultdict(set)

    for c in commits:
        for f in c.files_changed:
            parts = f.split("/")
            if len(parts) < 2:
                continue
            top_dir = parts[0]
            if top_dir not in dir_first_seen:
                dir_first_seen[top_dir] = c.timestamp
            dir_last_seen[top_dir] = c.timestamp
            dir_commits[top_dir] += 1
            dir_files[top_dir].add(f)

    # find the most recent commit date to determine if a dir is still "alive"
    if not commits:
        return []
    latest = max(c.timestamp for c in commits)

    ghost_systems: list[GhostSystem] = []
    for d, last in dir_last_seen.items():
        first = dir_first_seen[d]
        lifespan_days = (last - first).days
        commits_count = dir_commits[d]

        # must have existed 30+ days, had 10+ commits, and gone quiet before the latest commit
        days_since_last = (latest - last).days
        if lifespan_days >= 30 and commits_count >= 10 and days_since_last > 60:
            ghost_systems.append(GhostSystem(
                name=d,
                existed_from=first,
                deleted_on=last,
                files=sorted(dir_files[d])[:20],
                description="",  # filled in by LLM
            ))

    return ghost_systems


def get_commits_in_range(commits: list[Commit], start: datetime, end: datetime) -> list[Commit]:
    return [c for c in commits if start <= c.timestamp <= end]


def get_dominant_contributors(commits: list[Commit], top_n: int = 3) -> list[str]:
    counts: dict[str, int] = defaultdict(int)
    for c in commits:
        counts[c.author_name] += 1
    return [name for name, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]]


def summarize_top_files(commits: list[Commit], top_n: int = 10) -> list[str]:
    churn = compute_file_churn(commits)
    return list(churn.keys())[:top_n]
