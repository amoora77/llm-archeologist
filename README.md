# Code Archeologist

> Uncover the history buried in your git log.

Code Archeologist takes any public GitHub repository and produces a magazine-style narrative report about its entire history — written by an AI that reads the git log the way a historian reads primary sources.

---

## What it produces

Paste a GitHub URL. Wait a few minutes. Get a report with:

- **Origin Story** — how the project began, what problem it was solving, what the earliest architectural decisions were
- **The Eras** — automatically detected phases of the project's life, each with a title and narrative
- **The Pivots** — moments where the architecture shifted: rewrites, migrations, deprecations
- **The Characters** — a profile of each significant contributor and the fingerprints they left on the codebase
- **Ghost Code** — systems that were built, had real commits, and were then deleted entirely
- **Dark Periods** — weeks of intense, late-night activity that often signal deadlines or crises
- **The Archeologist's Note** — an editorial opinion on what this codebase's history says about the team that built it

---

## Stack

**Backend**
- Python 3.14 + FastAPI + Uvicorn
- `gitpython` for git history traversal
- Anthropic SDK (`claude-sonnet-4-6`) for all LLM calls with prompt caching
- SQLite for report caching (re-analysis is instant if the repo hasn't changed)
- SSE for real-time progress streaming

**Frontend**
- Next.js 16 (App Router)
- Tailwind CSS + shadcn/ui
- Recharts for the era timeline visualization
- Framer Motion for animations

---

## Running locally

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- [Bun](https://bun.sh)
- An [Anthropic API key](https://console.anthropic.com)

### Backend

```bash
cd backend
uv sync
cp .env.example .env
# add your Anthropic API key to .env
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
bun install
bun dev
```

Open [http://localhost:3000](http://localhost:3000), paste a GitHub URL, and hit **Analyze**.

---

## How it works

1. **Extraction** — clones the repo and walks every commit, capturing metadata, file-level diffs, and change stats. For repos with >10k commits, it samples intelligently: always keeping the first and last 100 commits and all high-signal commits (large diffs, many files touched).

2. **Processing** — detects era boundaries using rolling commit frequency analysis, computes contributor stats, identifies ghost systems (directories that accumulated commits and then went silent), and finds dark periods (weeks with 3× the normal commit rate).

3. **LLM Pipeline** — passes structured, compressed representations of the history to Claude. Each era, contributor, pivot, and ghost system gets its own focused prompt. The system prompt and repo context are cached across calls using Anthropic's prompt caching, cutting cost by ~60%.

4. **Synthesis** — a final pass generates the origin story and the archeologist's note, tying everything together into a coherent narrative.

5. **Report** — served as a Next.js page with a recharts timeline and all narrative sections. Also exportable as a standalone HTML file.

---

## Project structure

```
code-archeologist/
├── backend/
│   ├── main.py          # FastAPI app, SSE streaming, HTML export
│   ├── extractor.py     # Git history extraction and sampling
│   ├── processor.py     # Era detection, contributor stats, ghost systems
│   ├── summarizer.py    # Per-era and per-contributor LLM calls
│   ├── narrator.py      # Origin story, synthesis, full report assembly
│   ├── prompts.py       # All LLM prompt templates
│   ├── cache.py         # SQLite caching layer
│   └── models.py        # Dataclasses for the full report schema
└── frontend/
    ├── app/
    │   ├── page.tsx                    # Landing page
    │   ├── analyze/[jobId]/page.tsx    # SSE progress view
    │   └── report/[id]/page.tsx        # Full report view
    └── components/
        ├── ReportHero.tsx
        ├── Timeline.tsx
        ├── EraCard.tsx
        ├── ContributorProfile.tsx
        ├── GhostCodeSection.tsx
        ├── StatsBar.tsx
        └── NarrativeBlock.tsx
```

---

## Caching

Reports are cached in `backend/cache.db` keyed by `repo URL + latest commit hash`. If you analyze the same repo twice and nothing has changed, the cached report is returned instantly with no API calls.
