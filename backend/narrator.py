import json
import os
from datetime import datetime
from typing import Callable, Awaitable

import anthropic

from models import Commit, Contributor, Era, GhostSystem, Pivot, RepoReport
from prompts import ORIGIN_STORY_PROMPT, FINAL_SYNTHESIS_PROMPT
from processor import (
    compute_contributor_stats,
    compute_file_churn,
    detect_dark_periods,
    detect_eras,
    get_commits_in_range,
    get_dominant_contributors,
    identify_ghost_systems,
)
from summarizer import (
    _fmt_commits,
    _system_block,
    classify_pivot,
    generate_contributor_profile,
    narrate_ghost_system,
    summarize_era,
)

MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

ProgressCallback = Callable[[str, str], Awaitable[None]]


async def generate_origin_story(
    commits: list[Commit],
    initial_file_tree: list[str],
    initial_readme: str,
    repo_name: str,
    repo_url: str,
    total_commits: int,
    total_contributors: int,
    top_churned: list[str],
) -> str:
    first_author = commits[0].author_name if commits else "unknown"
    first_commit_date = commits[0].timestamp.strftime("%Y-%m-%d") if commits else "unknown"
    latest_date = commits[-1].timestamp.strftime("%Y-%m-%d") if commits else "unknown"

    current_state_summary = (
        f"As of {latest_date}, the repository has {total_commits} total commits "
        f"from {total_contributors} contributors. "
        f"Most-modified files: {', '.join(top_churned[:5])}."
    )

    prompt = ORIGIN_STORY_PROMPT.format(
        repo_name=repo_name,
        repo_url=repo_url,
        first_commit_date=first_commit_date,
        first_author=first_author,
        first_commits=_fmt_commits(commits[:10], max_count=10),
        initial_file_tree="\n".join(f"  {f}" for f in initial_file_tree[:60]),
        initial_readme=initial_readme[:2000] if initial_readme else "(no README found)",
        current_state_summary=current_state_summary,
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        temperature=0.7,
        system=[_system_block()],
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


async def generate_synthesis(
    eras: list[Era],
    pivots: list[Pivot],
    contributors: list[Contributor],
    ghost_systems: list[GhostSystem],
    dark_periods: list[dict],
    total_commits: int,
    total_contributors: int,
    first_commit: datetime,
    latest_commit: datetime,
    top_churned: list[str],
    current_file_count: int,
    repo_name: str,
) -> dict:
    era_summaries = "\n\n".join(
        f"Era: {e.title} ({e.start_date.strftime('%Y-%m-%d')} to {e.end_date.strftime('%Y-%m-%d')})\n"
        f"Key events: {'; '.join(e.key_events)}\n"
        f"Summary: {e.narrative}"
        for e in eras
    ) or "No eras detected."

    pivot_summaries = "\n\n".join(
        f"[{p.date.strftime('%Y-%m-%d')}] {p.title} ({p.category})\n{p.description}"
        for p in pivots
    ) or "No major pivots detected."

    contributor_profiles = "\n\n".join(
        f"{c.name} ({c.commit_count} commits, "
        f"{c.first_commit.strftime('%Y-%m')} to {c.last_commit.strftime('%Y-%m')})\n{c.profile}"
        for c in contributors
    ) or "No contributor profiles generated."

    ghost_system_summaries = "\n\n".join(
        f"{g.name} (existed {g.existed_from.strftime('%Y-%m-%d')} to {g.deleted_on.strftime('%Y-%m-%d')})\n{g.description}"
        for g in ghost_systems
    ) or "No ghost systems detected."

    dark_period_summaries = "\n".join(
        f"Week of {dp['week']}: {dp['commit_count']} commits "
        f"({dp['intensity_ratio']}x normal), {dp['late_night_commits']} late-night, "
        f"contributors: {', '.join(dp['contributors'])}"
        for dp in dark_periods
    ) or "No unusual dark periods detected."

    prompt = FINAL_SYNTHESIS_PROMPT.format(
        repo_name=repo_name,
        era_summaries=era_summaries,
        pivot_summaries=pivot_summaries,
        contributor_profiles=contributor_profiles,
        ghost_systems=ghost_system_summaries,
        dark_periods=dark_period_summaries,
        total_commits=total_commits,
        total_contributors=total_contributors,
        first_commit=first_commit.strftime("%Y-%m-%d"),
        latest_commit=latest_commit.strftime("%Y-%m-%d"),
        top_churned=", ".join(top_churned[:10]),
        file_count=current_file_count,
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        temperature=0.7,
        system=[_system_block()],
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


async def assemble_report(
    commits: list[Commit],
    repo_url: str,
    repo_name: str,
    mass_deletions: list[dict],
    initial_file_tree: list[str],
    initial_readme: str,
    current_file_count: int,
    progress_callback: ProgressCallback | None = None,
) -> RepoReport:
    async def progress(status: str, message: str) -> None:
        if progress_callback:
            await progress_callback(status, message)

    # --- Phase 1: local processing (no LLM) ---
    await progress("processing", "Detecting eras and contributors...")
    era_ranges = detect_eras(commits)
    contributor_stats = compute_contributor_stats(commits)
    file_churn = compute_file_churn(commits)
    dark_periods = detect_dark_periods(commits)
    ghost_systems_raw = identify_ghost_systems(commits)

    top_churned = list(file_churn.keys())[:20]
    total_commits = len(commits)
    total_contributors = len(contributor_stats)
    first_commit_dt = commits[0].timestamp if commits else datetime.now()
    latest_commit_dt = commits[-1].timestamp if commits else datetime.now()

    repo_context = (
        f"{repo_name} — {total_commits} commits from {total_contributors} contributors, "
        f"{first_commit_dt.strftime('%Y')} to {latest_commit_dt.strftime('%Y')}. "
        f"Top churned files: {', '.join(top_churned[:5])}."
    )

    # --- Phase 2: era summarization ---
    eras: list[Era] = []
    for i, (start, end) in enumerate(era_ranges):
        await progress("analyzing", f"Generating era narratives ({i + 1}/{len(era_ranges)})...")
        era_commits = get_commits_in_range(commits, start, end)
        dominant = get_dominant_contributors(era_commits)
        era_data = await summarize_era(era_commits, start, end, repo_name, repo_context)
        eras.append(Era(
            title=era_data.get("title", f"Era {i + 1}"),
            start_date=start,
            end_date=end,
            commit_count=len(era_commits),
            dominant_contributors=dominant,
            key_events=era_data.get("key_events", []),
            narrative=era_data.get("summary", ""),
        ))

    # --- Phase 3: contributor profiles (top 10) ---
    await progress("analyzing", "Profiling contributors...")
    top_stats = sorted(contributor_stats.values(), key=lambda s: s.commit_count, reverse=True)[:10]
    contributors: list[Contributor] = []
    for stats in top_stats:
        profile_text = await generate_contributor_profile(stats, repo_name)
        contributors.append(Contributor(
            name=stats.name,
            email=stats.email,
            commit_count=stats.commit_count,
            first_commit=stats.first_commit,
            last_commit=stats.last_commit,
            primary_areas=stats.primary_areas,
            signature_files=stats.signature_files,
            profile=profile_text,
        ))

    # --- Phase 4: pivot classification ---
    pivots: list[Pivot] = []
    if mass_deletions:
        await progress("analyzing", "Classifying architectural pivots...")
        commit_by_hash = {c.hash: i for i, c in enumerate(commits)}
        for event in mass_deletions[:10]:
            idx = commit_by_hash.get(event.get("hash", ""), 0)
            prior = commits[max(0, idx - 50): idx]
            try:
                pivot_data = await classify_pivot(event, prior, repo_name)
                raw_date = event.get("date", datetime.now())
                event_date = raw_date if isinstance(raw_date, datetime) else datetime.fromisoformat(str(raw_date))
                pivots.append(Pivot(
                    date=event_date,
                    title=pivot_data.get("title", "Unknown Pivot"),
                    description=pivot_data.get("description", ""),
                    evidence=event.get("files_changed", [])[:5],
                    category=pivot_data.get("category", "unknown"),
                    significance=pivot_data.get("significance", "medium"),
                ))
            except Exception:
                pass

    # --- Phase 5: ghost system narration ---
    ghost_systems: list[GhostSystem] = []
    if ghost_systems_raw:
        await progress("analyzing", "Narrating ghost systems...")
        for ghost in ghost_systems_raw[:8]:
            try:
                ghost.description = await narrate_ghost_system(ghost, repo_name, commits)
            except Exception:
                ghost.description = "A system whose purpose has been lost to time."
            ghost_systems.append(ghost)

    # --- Phase 6: origin story ---
    await progress("analyzing", "Writing origin story...")
    origin_story = await generate_origin_story(
        commits, initial_file_tree, initial_readme,
        repo_name, repo_url, total_commits, total_contributors, top_churned,
    )

    # --- Phase 7: final synthesis ---
    await progress("analyzing", "Writing final synthesis...")
    synthesis = await generate_synthesis(
        eras, pivots, contributors, ghost_systems, dark_periods,
        total_commits, total_contributors, first_commit_dt, latest_commit_dt,
        top_churned, current_file_count, repo_name,
    )

    await progress("complete", "Report ready.")

    return RepoReport(
        repo_url=repo_url,
        repo_name=repo_name,
        analysis_date=datetime.now(),
        total_commits=total_commits,
        total_contributors=total_contributors,
        first_commit=first_commit_dt,
        latest_commit=latest_commit_dt,
        origin_story=origin_story,
        eras=eras,
        contributors=contributors,
        pivots=pivots,
        ghost_systems=ghost_systems,
        dark_periods=dark_periods,
        present_state=synthesis.get("present_state", ""),
        archeologists_note=synthesis.get("archeologists_note", ""),
        top_churned_files=top_churned[:10],
    )
