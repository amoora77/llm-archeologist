from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Commit:
    hash: str
    author_name: str
    author_email: str
    timestamp: datetime
    message: str
    files_changed: list[str]
    insertions: int
    deletions: int
    is_merge: bool


@dataclass
class Era:
    title: str
    start_date: datetime
    end_date: datetime
    commit_count: int
    dominant_contributors: list[str]
    key_events: list[str]
    narrative: str


@dataclass
class Contributor:
    name: str
    email: str
    commit_count: int
    first_commit: datetime
    last_commit: datetime
    primary_areas: list[str]
    signature_files: list[str]
    profile: str


@dataclass
class Pivot:
    date: datetime
    title: str
    description: str
    evidence: list[str]
    category: str = "unknown"
    significance: str = "medium"


@dataclass
class GhostSystem:
    name: str
    existed_from: datetime
    deleted_on: datetime
    files: list[str]
    description: str


@dataclass
class ContributorStats:
    name: str
    email: str
    commit_count: int
    first_commit: datetime
    last_commit: datetime
    files_touched: set[str] = field(default_factory=set)
    dir_counts: dict[str, int] = field(default_factory=dict)
    file_commit_counts: dict[str, int] = field(default_factory=dict)
    notable_commits: list["Commit"] = field(default_factory=list)

    @property
    def primary_areas(self) -> list[str]:
        sorted_dirs = sorted(self.dir_counts.items(), key=lambda x: x[1], reverse=True)
        return [d for d, _ in sorted_dirs[:5]]

    @property
    def signature_files(self) -> list[str]:
        return [f for f, _ in sorted(
            self.file_commit_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]]


@dataclass
class RepoReport:
    repo_url: str
    repo_name: str
    analysis_date: datetime
    total_commits: int
    total_contributors: int
    first_commit: datetime
    latest_commit: datetime
    origin_story: str
    eras: list[Era]
    contributors: list[Contributor]
    pivots: list[Pivot]
    ghost_systems: list[GhostSystem]
    dark_periods: list[dict[str, Any]]
    present_state: str
    archeologists_note: str = ""
    top_churned_files: list[str] = field(default_factory=list)
