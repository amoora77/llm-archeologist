import subprocess
import random
from datetime import datetime
from pathlib import Path

import git

from models import Commit


def _parse_timestamp(ts: int) -> datetime:
    return datetime.utcfromtimestamp(ts)


def _is_merge(commit: git.Commit) -> bool:
    return len(commit.parents) > 1


def _get_diff_stats(commit: git.Commit) -> tuple[list[str], int, int]:
    if not commit.parents:
        files = list(commit.stats.files.keys())
        insertions = commit.stats.total["insertions"]
        deletions = commit.stats.total["deletions"]
        return files, insertions, deletions

    parent = commit.parents[0]
    diff = parent.diff(commit)
    files = []
    insertions = 0
    deletions = 0
    for d in diff:
        path = d.b_path or d.a_path
        if path:
            files.append(path)
    stats = commit.stats.total
    insertions = stats.get("insertions", 0)
    deletions = stats.get("deletions", 0)
    return files, insertions, deletions


def extract_full_history(repo_path: str) -> list[Commit]:
    repo = git.Repo(repo_path)
    try:
        head = repo.head.commit
    except Exception:
        return []

    all_commits = list(repo.iter_commits(head))
    all_commits.reverse()  # chronological order

    total = len(all_commits)

    if total <= 10_000:
        selected = all_commits
    else:
        first_100 = all_commits[:100]
        last_100 = all_commits[-100:]
        middle = all_commits[100:-100]

        high_signal = []
        rest = []
        for c in middle:
            stats = c.stats.total
            if stats.get("files", 0) > 10 or (stats.get("insertions", 0) + stats.get("deletions", 0)) > 500:
                high_signal.append(c)
            else:
                rest.append(c)

        sampled_rest = random.sample(rest, k=int(len(rest) * 0.2))
        selected = first_100 + high_signal + sampled_rest + last_100

    result: list[Commit] = []
    for c in selected:
        try:
            files, ins, dels = _get_diff_stats(c)
            result.append(Commit(
                hash=c.hexsha,
                author_name=c.author.name or "",
                author_email=c.author.email or "",
                timestamp=_parse_timestamp(c.authored_date),
                message=c.message.strip(),
                files_changed=files,
                insertions=ins,
                deletions=dels,
                is_merge=_is_merge(c),
            ))
        except Exception:
            continue

    return result


def extract_file_tree_at_dates(repo_path: str, dates: list[datetime]) -> dict[str, list[str]]:
    repo = git.Repo(repo_path)
    result: dict[str, list[str]] = {}

    all_commits = list(repo.iter_commits(repo.head.commit))
    all_commits.sort(key=lambda c: c.authored_date)

    for target_date in dates:
        ts = target_date.timestamp()
        closest = None
        for c in all_commits:
            if c.authored_date <= ts:
                closest = c
            else:
                break

        if closest is None:
            result[target_date.isoformat()] = []
            continue

        try:
            files = []
            for blob in closest.tree.traverse():
                if blob.type == "blob":
                    files.append(blob.path)
            result[target_date.isoformat()] = files
        except Exception:
            result[target_date.isoformat()] = []

    return result


def detect_mass_deletions(commits: list[Commit]) -> list[dict]:
    events = []
    for c in commits:
        deleted_files = [f for f in c.files_changed if not Path(f).suffix or True]
        if c.deletions > 1000 or len(c.files_changed) > 20:
            events.append({
                "hash": c.hash,
                "date": c.timestamp,
                "message": c.message,
                "files_changed": c.files_changed,
                "insertions": c.insertions,
                "deletions": c.deletions,
            })
    return events


def detect_renames(repo_path: str) -> list[dict]:
    result = subprocess.run(
        ["git", "log", "--diff-filter=R", "--summary", "--format=%H %ai %s"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    renames = []
    current_commit: dict | None = None
    for line in result.stdout.splitlines():
        if line and not line.startswith(" ") and not line.startswith("rename"):
            parts = line.split(" ", 3)
            if len(parts) >= 4:
                current_commit = {"hash": parts[0], "date": parts[1], "message": parts[3], "renames": []}
                renames.append(current_commit)
        elif line.strip().startswith("rename") and current_commit is not None:
            current_commit["renames"].append(line.strip())
    return [r for r in renames if r.get("renames")]


def clone_repo(url: str, target_dir: str) -> str:
    repo_name = url.rstrip("/").split("/")[-1].removesuffix(".git")
    dest = Path(target_dir) / repo_name
    if dest.exists():
        return str(dest)
    git.Repo.clone_from(url, str(dest))
    return str(dest)
