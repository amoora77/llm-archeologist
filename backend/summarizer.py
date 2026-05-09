import json
import os
from datetime import datetime

import anthropic

from models import Commit, ContributorStats, Era, Pivot, GhostSystem
from prompts import (
    SYSTEM_PROMPT,
    ERA_PROMPT,
    CONTRIBUTOR_PROMPT,
    PIVOT_PROMPT,
    GHOST_SYSTEM_PROMPT,
)

MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def _fmt_commits(commits: list[Commit], max_count: int = 50) -> str:
    sample = commits[:max_count]
    lines = []
    for c in sample:
        lines.append(
            f"[{c.timestamp.strftime('%Y-%m-%d')}] {c.author_name}: {c.message[:120]}"
            f" (+{c.insertions}/-{c.deletions}, {len(c.files_changed)} files)"
        )
    return "\n".join(lines)


def _system_block() -> dict:
    return {
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }


async def summarize_era(
    era_commits: list[Commit],
    era_start: datetime,
    era_end: datetime,
    repo_name: str,
    repo_context: str,
) -> dict:
    top_files: dict[str, int] = {}
    for c in era_commits:
        for f in c.files_changed:
            top_files[f] = top_files.get(f, 0) + 1
    top_files_str = "\n".join(
        f"  {f} ({n} changes)"
        for f, n in sorted(top_files.items(), key=lambda x: x[1], reverse=True)[:10]
    )

    contributors = list({c.author_name for c in era_commits})
    prompt = ERA_PROMPT.format(
        repo_name=repo_name,
        start_date=era_start.strftime("%Y-%m-%d"),
        end_date=era_end.strftime("%Y-%m-%d"),
        count=len(era_commits),
        commit_summary=_fmt_commits(era_commits),
        top_files=top_files_str,
        contributors=", ".join(contributors),
        repo_context=repo_context,
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        temperature=0.7,
        system=[_system_block()],
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    # strip possible markdown code fences
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


async def generate_contributor_profile(
    stats: ContributorStats,
    repo_name: str,
) -> str:
    notable = _fmt_commits(stats.notable_commits, max_count=10)
    prompt = CONTRIBUTOR_PROMPT.format(
        repo_name=repo_name,
        name=stats.name,
        first_commit_date=stats.first_commit.strftime("%Y-%m-%d"),
        last_commit_date=stats.last_commit.strftime("%Y-%m-%d"),
        commit_count=stats.commit_count,
        primary_dirs=", ".join(stats.primary_areas) or "various",
        signature_files=", ".join(stats.signature_files[:5]) or "various",
        notable_commits=notable or "(no large commits recorded)",
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        temperature=0.7,
        system=[_system_block()],
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


async def classify_pivot(
    event: dict,
    prior_commits: list[Commit],
    repo_name: str,
) -> dict:
    prior_context = _fmt_commits(prior_commits[-20:], max_count=20)
    files = event.get("files_changed", [])
    prompt = PIVOT_PROMPT.format(
        repo_name=repo_name,
        date=event["date"].strftime("%Y-%m-%d") if isinstance(event["date"], datetime) else event["date"],
        message=event.get("message", "")[:200],
        deleted_files=", ".join(f for f in files if f) or "none",
        added_files="(see files_changed)",
        renamed_files="(see detect_renames output)",
        deletions=event.get("deletions", 0),
        insertions=event.get("insertions", 0),
        prior_context=prior_context,
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        temperature=0.5,
        system=[_system_block()],
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


async def narrate_ghost_system(
    ghost: GhostSystem,
    repo_name: str,
    nearby_commits: list[Commit],
) -> str:
    lifespan_days = (ghost.deleted_on - ghost.existed_from).days
    final_commits = [
        c for c in nearby_commits
        if any(ghost.name in f for f in c.files_changed)
    ]
    prompt = GHOST_SYSTEM_PROMPT.format(
        repo_name=repo_name,
        name=ghost.name,
        existed_from=ghost.existed_from.strftime("%Y-%m-%d"),
        deleted_on=ghost.deleted_on.strftime("%Y-%m-%d"),
        lifespan_days=lifespan_days,
        commit_count=len([
            c for c in nearby_commits
            if any(ghost.name in f for f in c.files_changed)
        ]),
        files="\n".join(f"  {f}" for f in ghost.files[:15]),
        final_commits=_fmt_commits(final_commits[-10:], max_count=10),
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        temperature=0.7,
        system=[_system_block()],
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
