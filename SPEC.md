# Code Archeologist — Full Project Specification & Build Prompt

## Overview

Build a tool called **Code Archeologist** that accepts a GitHub repository URL (or local path), analyzes its entire git history using LLMs, and produces a rich, beautifully formatted narrative report about the codebase's evolution. The output should read like a long-form magazine article — not a dry changelog, but an actual *story* about how the software came to be.

This is a portfolio-grade project. Every component should be well-engineered, the UI should look stunning, and the output should be impressive enough to share publicly.

---

## What the Output Looks Like

The final report is a shareable HTML page (or rendered web view) with the following sections:

### 1. The Origin Story
How the repo was born. Who wrote the first commit. What the initial architecture looked like. What the earliest intentions were (inferred from directory names, README content, early commit messages).

### 2. The Eras
A timeline broken into distinct "eras" — identified automatically by analyzing changes in commit frequency, contributor patterns, and file structure shifts. Each era gets a title and a narrative paragraph. Example eras might be:
- "The Prototype Phase (Jan–Mar 2019)"
- "The Great Rewrite (Aug 2020)"
- "Stabilization & Scale (2021–2022)"

### 3. The Pivots
Moments where the architecture changed significantly. Detected by: large-scale file deletions/renames, sudden introduction of new directories, removal of major dependencies, rewrites of core files. These are the most interesting moments in any codebase's life.

### 4. The Characters
A profile for each significant contributor. Not just "X made 847 commits" — but what they worked on, what their "signature" parts of the codebase are, and how their involvement changed over time.

### 5. Ghost Code
Features, systems, and experiments that were built and then deleted. These are often the most interesting parts of a codebase's history — abandoned approaches, deprecated modules, entire systems that didn't make the cut.

### 6. The Dark Periods
Stretches of intense activity — inferred from commit frequency spikes, late-night commits, and mass changes. These often correspond to deadlines, incidents, or crisis rewrites.

### 7. The Present
How the current architecture came to be. A summary of the current state and how it evolved from the origin.

---

## Technical Architecture

### Stack

**Backend:**
- Python 3.11+
- `gitpython` — git repo access and history traversal
- `anthropic` SDK — Claude API for all LLM calls (use `claude-sonnet-4-6`)
- `fastapi` — web server for the UI backend
- `uvicorn` — ASGI server
- `sqlite3` (stdlib) — caching processed repo data so re-analysis is instant
- `subprocess` — for raw git commands where gitpython falls short

**Frontend:**
- Next.js 14 (App Router)
- Tailwind CSS
- `shadcn/ui` components
- `recharts` — for timeline and contributor charts
- `framer-motion` — for animations and section transitions

**Dev tooling:**
- `uv` for Python dependency management
- `bun` for JS dependency management

### Repository Structure

```
code-archeologist/
├── SPEC.md                  # This file
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── extractor.py         # Git history extraction logic
│   ├── processor.py         # Data processing, era detection, stats
│   ├── summarizer.py        # LLM summarization pipeline
│   ├── narrator.py          # LLM narrative generation
│   ├── cache.py             # SQLite caching layer
│   ├── models.py            # Pydantic data models
│   └── prompts.py           # All LLM prompt templates
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Landing page / URL input
│   │   ├── report/
│   │   │   └── [id]/
│   │   │       └── page.tsx # Report view
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ReportHero.tsx
│   │   ├── Timeline.tsx
│   │   ├── EraCard.tsx
│   │   ├── ContributorProfile.tsx
│   │   ├── GhostCodeSection.tsx
│   │   ├── StatsBar.tsx
│   │   └── NarrativeBlock.tsx
│   └── lib/
│       └── api.ts
└── README.md
```

---

## Data Models

```python
# models.py

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
    title: str                    # LLM-generated, e.g. "The Prototype Phase"
    start_date: datetime
    end_date: datetime
    commit_count: int
    dominant_contributors: list[str]
    key_events: list[str]         # bullet points of notable moments
    narrative: str                # LLM-generated paragraph

@dataclass
class Contributor:
    name: str
    email: str
    commit_count: int
    first_commit: datetime
    last_commit: datetime
    primary_areas: list[str]      # directories they most touched
    signature_files: list[str]    # files they are the primary author of
    profile: str                  # LLM-generated contributor narrative

@dataclass
class Pivot:
    date: datetime
    title: str                    # e.g. "Migration from REST to GraphQL"
    description: str              # LLM-generated
    evidence: list[str]           # specific commits/files that signal this

@dataclass
class GhostSystem:
    name: str                     # e.g. "The old authentication module"
    existed_from: datetime
    deleted_on: datetime
    files: list[str]
    description: str              # LLM-generated

@dataclass
class RepoReport:
    repo_url: str
    repo_name: str
    analysis_date: datetime
    total_commits: int
    total_contributors: int
    first_commit: datetime
    latest_commit: datetime
    origin_story: str             # LLM-generated
    eras: list[Era]
    contributors: list[Contributor]
    pivots: list[Pivot]
    ghost_systems: list[GhostSystem]
    dark_periods: list[dict]
    present_state: str            # LLM-generated
```

---

## Data Pipeline

### Phase 1: Extraction (`extractor.py`)

Extract the following from the git repo:

```python
def extract_full_history(repo_path: str) -> list[Commit]:
    """
    Walk every commit in the repo's main branch.
    For each commit, capture:
    - Full metadata (hash, author, date, message)
    - File-level diff stats (which files changed, +/- lines)
    - Whether it's a merge commit
    
    For large repos (>10k commits), sample intelligently:
    - Always include first 100 commits
    - Always include last 100 commits  
    - For middle commits, include all commits that touch >10 files
      or have >500 line changes, sample the rest at 20%
    """

def extract_file_tree_at_dates(repo, dates: list[datetime]) -> dict[datetime, list[str]]:
    """
    Get a snapshot of the file tree at key moments in time.
    Used to detect structural shifts in the codebase.
    """

def detect_mass_deletions(commits: list[Commit]) -> list[dict]:
    """
    Find commits where >20 files were deleted or >1000 lines were removed.
    These are high-signal events (rewrites, deprecations, cleanups).
    """

def detect_renames(repo) -> list[dict]:
    """
    Use git log --follow to find major file/directory renames.
    """
```

### Phase 2: Processing (`processor.py`)

```python
def detect_eras(commits: list[Commit]) -> list[tuple[datetime, datetime]]:
    """
    Use a simple change-point detection algorithm on weekly commit frequency.
    A new era begins when commit frequency changes by >50% sustained over 3+ weeks,
    or when the dominant contributor changes, or when >30% of files are new.
    Target: 3-7 eras for most repos.
    """

def compute_contributor_stats(commits: list[Commit]) -> dict[str, ContributorStats]:
    """
    Per contributor: commit count, date range, files touched,
    primary directories, files where they are the majority author.
    """

def compute_file_churn(commits: list[Commit]) -> dict[str, int]:
    """
    How many times each file was modified. Top churned files are
    often the core of the system — or its biggest problems.
    """

def detect_dark_periods(commits: list[Commit]) -> list[dict]:
    """
    Weeks where commit frequency is >3x the rolling average.
    Also look for commit timestamps between 10pm and 4am as a signal.
    """

def identify_ghost_systems(commits: list[Commit]) -> list[GhostSystem]:
    """
    Find directories or file groups that existed for >30 days,
    had >10 commits touching them, and were then entirely deleted.
    These are ghost systems worth narrating.
    """
```

### Phase 3: Summarization (`summarizer.py`)

This is where the LLM pipeline begins. All calls go through Claude via the Anthropic SDK with prompt caching enabled on static context.

```python
async def summarize_era(era_commits: list[Commit], repo_context: str) -> EraLabels:
    """
    Given commits in a time window, ask Claude to:
    1. Give the era a evocative title
    2. Identify 3-5 key events/themes in bullet form
    3. Write a 2-3 sentence summary
    
    Uses claude-sonnet-4-6.
    """

async def generate_contributor_profile(stats: ContributorStats, notable_commits: list[Commit]) -> str:
    """
    Given a contributor's stats and their most notable commits (biggest diffs,
    most impactful changes), write a 2-3 sentence profile.
    """

async def classify_pivots(mass_changes: list[dict], context: str) -> list[Pivot]:
    """
    Given detected large structural changes, ask Claude to classify each as:
    - Architecture pivot
    - Technology migration  
    - Feature expansion
    - Cleanup/deprecation
    - Incident response
    And write a description of what happened.
    """
```

### Phase 4: Narrative Generation (`narrator.py`)

```python
async def generate_full_report(processed_data: dict) -> RepoReport:
    """
    Final synthesis step. Passes all era summaries, contributor profiles,
    pivots, ghost systems, and stats to Claude and asks for:
    1. Origin story (3-4 paragraphs)
    2. Present state summary (2-3 paragraphs)
    3. Final "archeologist's note" — an overall impression of the codebase
    
    This is the most expensive call. Use a larger context window.
    Uses claude-sonnet-4-6 with extended thinking if needed.
    """
```

---

## LLM Prompt Templates (`prompts.py`)

These are the exact prompts used in each LLM call. They are the most critical part of making the output actually interesting.

### System Prompt (shared across all calls)

```
You are a software historian and code archeologist. Your job is to analyze git history data and produce compelling, insightful narratives about how software projects evolved over time.

Your writing style is:
- Engaging and readable — like a long-form tech article, not a dry report
- Specific — you cite actual files, dates, commit messages as evidence
- Insightful — you look for patterns, ironies, and stories that aren't obvious from the surface
- Honest — you acknowledge when the evidence is thin or ambiguous

You never say things like "the commit history shows" or "according to the data." You write as if you have intimate knowledge of the project and are telling its story.

You avoid: bullet point lists in narrative sections, corporate jargon, vague statements like "significant changes were made."
```

### Era Summarization Prompt

```
Here is the git activity for a period in the {repo_name} repository, from {start_date} to {end_date}:

COMMITS ({count} total):
{commit_summary}

FILES MOST CHANGED IN THIS PERIOD:
{top_files}

CONTRIBUTORS ACTIVE:
{contributors}

REPOSITORY CONTEXT (overall project):
{repo_context}

---

Respond with a JSON object with these fields:
- "title": A short, evocative era title (4-8 words). Examples: "The Prototype Years", "The GraphQL Migration", "Scaling Pains". Make it specific to what actually happened.
- "key_events": An array of 3-5 strings, each a specific notable thing that happened in this era. Be concrete.
- "summary": 2-3 sentences narrating this era as part of the project's story.
```

### Contributor Profile Prompt

```
Here is data about a contributor to {repo_name}:

Name: {name}
First commit: {first_commit_date}
Last commit: {last_commit_date}  
Total commits: {commit_count}
Primary areas of the codebase: {primary_dirs}
Files they're the primary author of: {signature_files}

Their most significant commits (by lines changed):
{notable_commits}

---

Write a 2-3 sentence profile of this contributor as a software character. What did they build? What part of the codebase bears their fingerprints? How did their involvement change over time? Be specific and human — not a performance review.
```

### Pivot Classification Prompt

```
In {repo_name}, the following large structural change was detected:

Date: {date}
Commit message: {message}
Files deleted: {deleted_files}
Files added: {added_files}
Files renamed: {renamed_files}
Lines removed: {deletions}
Lines added: {insertions}

Recent context (commits in the 2 weeks before this):
{prior_context}

---

Respond with JSON:
- "title": A short title for this pivot (e.g. "Migration from Webpack to Vite", "Authentication Module Rewrite")
- "category": One of: "architecture_pivot", "technology_migration", "feature_expansion", "cleanup", "incident_response", "unknown"
- "description": 2-3 sentences describing what happened and why it mattered. If you're uncertain, say so.
- "significance": "high", "medium", or "low"
```

### Origin Story Prompt

```
You are writing the opening section of a code archeology report for: {repo_name}

Repository: {repo_url}
Created: {first_commit_date}
First author: {first_author}

First 10 commits:
{first_commits}

Initial file structure:
{initial_file_tree}

Initial README content (if any):
{initial_readme}

Current state summary:
{current_state_summary}

---

Write "The Origin Story" section of this report: 3-4 paragraphs about how this project began. Cover: what the first version looked like, what problem it was clearly trying to solve, what architectural decisions were made early on, and how those early choices echo in the current codebase. 

Write in past tense, in a compelling narrative voice. Reference specific files and dates as evidence.
```

### Final Synthesis Prompt

```
You are completing a code archeology report for {repo_name}.

Here is all the analysis you have:

ERAS:
{era_summaries}

MAJOR PIVOTS:
{pivot_summaries}

KEY CONTRIBUTORS:
{contributor_profiles}

GHOST SYSTEMS (built and deleted):
{ghost_systems}

DARK PERIODS (intense activity spikes):
{dark_periods}

STATISTICS:
- Total commits: {total_commits}
- Contributors: {total_contributors}  
- Lifespan: {first_commit} to {latest_commit}
- Most churned files: {top_churned}
- Current file count: {file_count}

---

Write two sections:

1. "The Present State" (2-3 paragraphs): How does the current architecture reflect the project's history? What decisions made early on are still visible? What was clearly added under pressure vs. thoughtfully designed?

2. "The Archeologist's Note" (1 paragraph): Your overall impression of this codebase as a historical artifact. What does its history say about the team, the product, or the problem it was solving? This is your editorial — be opinionated.
```

---

## API Design

### `POST /api/analyze`
```json
Request:
{
  "repo_url": "https://github.com/user/repo",
  "options": {
    "max_commits": 5000,
    "include_ghost_systems": true,
    "include_contributor_profiles": true
  }
}

Response (streaming SSE):
{ "status": "cloning", "message": "Cloning repository..." }
{ "status": "extracting", "message": "Extracting 3,421 commits..." }
{ "status": "processing", "message": "Detecting eras and pivots..." }
{ "status": "analyzing", "message": "Generating era narratives (1/5)..." }
{ "status": "complete", "report_id": "abc123" }
```

### `GET /api/report/{report_id}`
Returns the full `RepoReport` JSON.

### `GET /api/report/{report_id}/html`
Returns a standalone, shareable HTML file of the report.

---

## Frontend Design

### Landing Page (`/`)
- Dark background (near-black, `#0a0a0a`)
- Centered, large headline: **"Code Archeologist"**
- Subheadline: "Uncover the history buried in your git log."
- Single input field for GitHub URL, styled like a terminal command
- Prominent "Analyze" button
- Below: 3 example repos with "View Report" links to pre-generated demos

### Analysis Progress View
- Full-screen progress overlay
- Real-time status updates streamed via SSE
- Animated progress bar
- Show "fun facts" while processing: e.g. "Did you know: {repo_name} has {X} commits between midnight and 4am?"

### Report View (`/report/[id]`)

Layout: Wide single-column, centered, max-width 860px, generous padding.

**Hero section:**
- Repo name as large display type
- Key stats in a horizontal bar: total commits | contributors | years active | languages
- "Generated by Code Archeologist" with date

**Section: Origin Story**
- Prose narrative, no headers — reads like an article

**Section: The Eras**
- Horizontal scrollable timeline visualization (recharts)
- Each era is a card below the timeline: title, date range, key events, narrative

**Section: The Pivots**
- Card grid, each card has: date, title, category badge, description

**Section: The Characters**
- For each significant contributor: name, date range, commit count, primary areas, LLM-written profile

**Section: Ghost Code**
- Styled differently — slightly muted, "archaeological find" aesthetic
- Each ghost system: name, lifespan, what it was

**Section: Dark Periods**
- Simple list with dates and context

**Section: Present State + Archeologist's Note**
- Present state as prose
- Archeologist's Note in a styled blockquote

**Shareable:**
- "Share Report" button copies a link
- "Export HTML" button downloads a self-contained HTML file

---

## Implementation Plan

### Phase 1 — Backend Core (do this first)
1. Set up Python project with `uv`, install dependencies
2. Build `extractor.py` — get git history extraction working for a test repo
3. Build `processor.py` — era detection, contributor stats, ghost system detection
4. Build `cache.py` — SQLite caching so you don't re-process repos
5. Build `models.py` — all Pydantic/dataclass models
6. Test the full extraction + processing pipeline on 3 real repos (small, medium, large)

### Phase 2 — LLM Pipeline
1. Build `prompts.py` with all prompt templates
2. Build `summarizer.py` — era summarization, contributor profiles, pivot classification
3. Build `narrator.py` — origin story and final synthesis
4. Implement prompt caching via Anthropic SDK `cache_control` on static context blocks
5. Add streaming support so the frontend gets real-time updates
6. Test and tune prompts until output quality is genuinely impressive

### Phase 3 — API
1. Build FastAPI app with SSE streaming endpoint
2. Add background job queue (use `asyncio` tasks for simplicity, not Celery)
3. Add rate limiting and basic input validation

### Phase 4 — Frontend
1. Set up Next.js project with Tailwind + shadcn/ui
2. Build landing page
3. Build progress/streaming view
4. Build report view — all sections
5. Build recharts timeline visualization
6. Add HTML export feature

### Phase 5 — Polish
1. Generate demo reports for 3 famous repos (React, FastAPI, sqlite)
2. Deploy backend to Railway or Render
3. Deploy frontend to Vercel
4. Write a compelling README with screenshots/GIFs of real reports

---

## Key Engineering Decisions

**Why SSE over WebSockets for streaming?**
Analysis takes 30-120 seconds. SSE is simpler, works over HTTP/1.1, doesn't need a WS upgrade, and is sufficient for one-way progress streaming.

**Why SQLite for caching?**
Zero ops overhead. Cache key is the repo URL + latest commit hash. If the repo hasn't changed, serve the cached report instantly. For a portfolio project this is completely sufficient.

**Why not just dump all commits into one LLM call?**
Even small repos have thousands of commits. The extraction + processing pipeline converts raw git data into structured, LLM-friendly summaries. The LLM only sees curated, compressed representations — not raw diffs. This keeps costs low and output quality high.

**Prompt caching strategy:**
The system prompt and repo context are marked with `cache_control: {"type": "ephemeral"}` so they're cached between successive API calls within one analysis job. This cuts cost ~60% on the summarization phase.

**Handling huge repos:**
For repos with >10k commits, apply the sampling strategy in `extractor.py`: keep all boundary commits (first/last 100) and all high-signal commits (large changes, many files touched), sample the rest. The narrative quality is not meaningfully impacted.

---

## Definition of Done

The project is complete when:

- [ ] A user can paste any public GitHub URL and get a full report in under 3 minutes
- [ ] The report narrative reads like it was written by someone who actually read the code, not generated by a template
- [ ] The UI looks polished enough to screenshot and share on Twitter
- [ ] Pre-generated demo reports for 3 well-known repos are accessible on the landing page
- [ ] The project is deployed and publicly accessible
- [ ] The README has a GIF/video demo and clearly explains what it does

---

## Notes on Making the Output Actually Good

The difference between a cool project and a forgettable one is output quality. The LLM output needs to be *specific* and *surprising*, not generic. A few techniques:

1. **Give the LLM actual evidence.** Don't summarize the commits before passing them in — pass the real commit messages, real file names, real line counts. Specificity in → specificity out.

2. **Use temperature ~0.7 for narrative sections.** Low enough to be coherent, high enough to be interesting.

3. **Iterate on prompts with real repos.** Run the prompts against `facebook/react`, `tiangolo/fastapi`, and `django/django` and read every output until it sounds genuinely interesting.

4. **The Archeologist's Note is the money section.** This should be the most opinionated, most interesting paragraph in the report. Prompt it explicitly to be opinionated.

5. **Ghost code is almost always the most interesting section.** Make sure the detection is good — if a directory had >5 commits and was then deleted, it's worth narrating.

---

## Build Progress

> Last updated: 2026-05-08

### Phase 1 — Backend Core
- [x] Set up Python project with `uv`, install dependencies (`backend/pyproject.toml`, `.venv`)
- [x] `backend/models.py` — all dataclasses (Commit, Era, Contributor, Pivot, GhostSystem, ContributorStats, RepoReport)
- [x] `backend/cache.py` — SQLite caching layer (init_db, get/store by cache key, job tracking)
- [ ] `backend/extractor.py` — **NEXT: git history extraction**
- [ ] `backend/processor.py` — era detection, contributor stats, ghost system detection
- [ ] Test extraction + processing pipeline on 3 real repos

### Phase 2 — LLM Pipeline
- [ ] `backend/prompts.py`
- [ ] `backend/summarizer.py`
- [ ] `backend/narrator.py`
- [ ] Prompt caching + streaming

### Phase 3 — API
- [ ] `backend/main.py` — FastAPI app with SSE endpoint

### Phase 4 — Frontend
- [ ] Next.js 14 project setup (bun, Tailwind, shadcn/ui)
- [ ] Landing page (`/`)
- [ ] Progress/streaming view
- [ ] Report view (`/report/[id]`) — all sections
- [ ] recharts timeline
- [ ] HTML export

### Phase 5 — Polish
- [ ] Demo reports for React, FastAPI, sqlite repos
- [ ] Deploy (Railway + Vercel)
- [ ] README with GIF demo

### Decisions Made During Build
- Python 3.14 (latest available via Homebrew) — uv-managed venv at `backend/.venv`
- venv activation: `source backend/.venv/bin/activate`
- Cache DB written to `backend/cache.db` (gitignored)
- `RepoReport` uses `archeologists_note` as a separate field from `present_state`
