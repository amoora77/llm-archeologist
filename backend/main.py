import asyncio
import dataclasses
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from cache import (
    create_job,
    get_cached_report,
    get_job,
    get_report_by_id,
    init_db,
    make_cache_key,
    store_report,
    update_job,
)
from extractor import (
    clone_repo,
    detect_mass_deletions,
    extract_file_tree_at_dates,
    extract_full_history,
)
from narrator import assemble_report

app = FastAPI(title="Code Archeologist")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory SSE queues: job_id → asyncio.Queue of SSE event dicts
_job_queues: dict[str, asyncio.Queue] = {}

init_db()


class AnalyzeRequest(BaseModel):
    repo_url: str
    options: dict = {}


def _report_to_dict(report: Any) -> dict[str, Any]:
    return json.loads(json.dumps(dataclasses.asdict(report), default=str))


async def _run_analysis(job_id: str, repo_url: str, options: dict) -> None:
    queue = _job_queues[job_id]

    async def progress(status: str, message: str) -> None:
        await queue.put({"status": status, "message": message})

    try:
        update_job(job_id, "running")

        await progress("cloning", f"Cloning {repo_url}...")
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = clone_repo(repo_url, tmpdir)
            repo_name = Path(repo_path).name

            await progress("extracting", "Extracting git history...")
            commits = extract_full_history(repo_path)

            if not commits:
                raise ValueError("No commits found in repository.")

            latest_hash = commits[-1].hash
            cache_key = make_cache_key(repo_url, latest_hash)

            cached = get_cached_report(cache_key)
            if cached:
                update_job(job_id, "complete", cache_key)
                await queue.put({"status": "complete", "report_id": cache_key})
                return

            await progress("extracting", f"Processing {len(commits):,} commits...")
            mass_deletions = detect_mass_deletions(commits)

            first_date = commits[0].timestamp
            file_trees = extract_file_tree_at_dates(repo_path, [first_date, commits[-1].timestamp])
            initial_file_tree = file_trees.get(first_date.isoformat(), [])
            current_file_count = len(file_trees.get(commits[-1].timestamp.isoformat(), []))

            initial_readme = ""
            for candidate in ("README.md", "README", "README.rst", "readme.md"):
                readme_path = Path(repo_path) / candidate
                if readme_path.exists():
                    initial_readme = readme_path.read_text(errors="replace")[:3000]
                    break

            max_commits = options.get("max_commits", 5000)
            if len(commits) > max_commits:
                commits = commits[:max_commits]

            report = await assemble_report(
                commits=commits,
                repo_url=repo_url,
                repo_name=repo_name,
                mass_deletions=mass_deletions,
                initial_file_tree=initial_file_tree,
                initial_readme=initial_readme,
                current_file_count=current_file_count,
                progress_callback=progress,
            )

            report_dict = _report_to_dict(report)
            store_report(cache_key, repo_url, report_dict)
            update_job(job_id, "complete", cache_key)
            await queue.put({"status": "complete", "report_id": cache_key})

    except Exception as exc:
        update_job(job_id, "failed")
        await queue.put({"status": "error", "message": str(exc)})
    finally:
        await asyncio.sleep(10)
        _job_queues.pop(job_id, None)


@app.post("/api/analyze")
async def start_analysis(req: AnalyzeRequest):
    job_id = str(uuid.uuid4())
    create_job(job_id, req.repo_url)
    _job_queues[job_id] = asyncio.Queue()
    asyncio.create_task(_run_analysis(job_id, req.repo_url, req.options))
    return {"job_id": job_id}


@app.get("/api/analyze/{job_id}/stream")
async def stream_job(job_id: str):
    if not get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    queue = _job_queues.get(job_id)

    async def event_generator() -> AsyncGenerator[str, None]:
        if queue is None:
            job_row = get_job(job_id)
            if job_row and job_row["status"] == "complete":
                yield f"data: {json.dumps({'status': 'complete', 'report_id': job_row['report_id']})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Job queue unavailable'})}\n\n"
            return

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("status") in ("complete", "error"):
                    break
            except asyncio.TimeoutError:
                yield 'data: {"status":"heartbeat"}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/report/{report_id}")
async def get_report(report_id: str):
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@app.get("/api/report/{report_id}/html", response_class=HTMLResponse)
async def get_report_html(report_id: str):
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return HTMLResponse(content=_render_html(report))


def _render_html(report: dict) -> str:
    repo_name = report.get("repo_name", "Unknown")
    origin = report.get("origin_story", "")
    present = report.get("present_state", "")
    note = report.get("archeologists_note", "")

    def paras(text: str) -> str:
        return "".join(f"<p>{p}</p>" for p in text.split("\n\n") if p.strip())

    eras_html = ""
    for era in report.get("eras", []):
        events = "".join(f"<li>{e}</li>" for e in era.get("key_events", []))
        eras_html += f"""
        <div class="card">
          <h3>{era.get('title', '')}</h3>
          <p class="meta">{era.get('start_date', '')[:10]} → {era.get('end_date', '')[:10]}
            &bull; {era.get('commit_count', 0):,} commits</p>
          <ul>{events}</ul>
          <p>{era.get('narrative', '')}</p>
        </div>"""

    contributors_html = ""
    for c in report.get("contributors", []):
        contributors_html += f"""
        <div class="card">
          <h3>{c.get('name', '')}</h3>
          <p class="meta">{c.get('commit_count', 0):,} commits &bull;
            {c.get('first_commit', '')[:10]} – {c.get('last_commit', '')[:10]}</p>
          <p>{c.get('profile', '')}</p>
        </div>"""

    ghost_html = ""
    for g in report.get("ghost_systems", []):
        ghost_html += f"""
        <div class="card ghost">
          <h3>{g.get('name', '')}</h3>
          <p class="meta">{g.get('existed_from', '')[:10]} – {g.get('deleted_on', '')[:10]}</p>
          <p>{g.get('description', '')}</p>
        </div>"""

    pivots_html = ""
    for p in report.get("pivots", []):
        category = p.get("category", "unknown").replace("_", " ")
        pivots_html += f"""
        <div class="card">
          <span class="badge">{category}</span>
          <h3>{p.get('title', '')}</h3>
          <p class="meta">{p.get('date', '')[:10]} &bull; significance: {p.get('significance', '')}</p>
          <p>{p.get('description', '')}</p>
        </div>"""

    dark_html = ""
    for dp in report.get("dark_periods", []):
        dark_html += (
            f"<li>Week of {dp.get('week', '')} — {dp.get('commit_count', 0)} commits "
            f"({dp.get('intensity_ratio', '')}× normal), "
            f"{dp.get('late_night_commits', 0)} late-night &bull; "
            f"{', '.join(dp.get('contributors', []))}</li>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{repo_name} — Code Archeologist</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0a0a0a; color: #e4e4e4; font-family: Georgia, serif; line-height: 1.75; }}
    .container {{ max-width: 860px; margin: 0 auto; padding: 4rem 2rem; }}
    h1 {{ font-size: 3rem; font-weight: 700; letter-spacing: -1px; margin-bottom: .5rem; }}
    h2 {{ font-size: 1rem; font-weight: 600; color: #666; text-transform: uppercase;
          letter-spacing: 3px; font-family: monospace; margin: 3.5rem 0 1.5rem; }}
    h3 {{ font-size: 1.15rem; font-weight: 600; margin-bottom: .3rem; color: #f0f0f0; }}
    p {{ margin-bottom: 1.1rem; color: #c4c4c4; }}
    .meta {{ font-family: monospace; font-size: .8rem; color: #555; margin-bottom: .75rem; }}
    .card {{ border: 1px solid #1c1c1c; border-radius: 8px; padding: 1.5rem;
             margin-bottom: 1.25rem; background: #111; }}
    .card.ghost {{ border-color: #2a1c1c; background: #0e0909; }}
    .badge {{ display: inline-block; font-family: monospace; font-size: .7rem;
              background: #162016; color: #5a9e5a; border-radius: 4px;
              padding: .15rem .55rem; margin-bottom: .5rem; text-transform: uppercase;
              letter-spacing: 1px; }}
    ul {{ padding-left: 1.4rem; color: #888; margin-bottom: .75rem; }}
    li {{ margin-bottom: .25rem; font-size: .95rem; }}
    blockquote {{ border-left: 3px solid #333; padding: 1.25rem 1.5rem;
                  margin: 1rem 0; color: #aaa; font-style: italic; background: #0e0e0e;
                  border-radius: 0 6px 6px 0; }}
    .stats-bar {{ display: flex; gap: 2.5rem; padding: 1.5rem 0;
                  border-top: 1px solid #1c1c1c; border-bottom: 1px solid #1c1c1c;
                  margin: 1.5rem 0 2rem; flex-wrap: wrap; }}
    .stat .val {{ font-family: monospace; font-size: 1.6rem; color: #fff; }}
    .stat .lbl {{ font-family: monospace; font-size: .7rem; color: #555;
                  text-transform: uppercase; letter-spacing: 1px; }}
    .footer {{ margin-top: 5rem; font-family: monospace; font-size: .75rem; color: #333; }}
  </style>
</head>
<body>
<div class="container">
  <h1>{repo_name}</h1>
  <div class="stats-bar">
    <div class="stat"><div class="val">{report.get('total_commits', 0):,}</div><div class="lbl">Commits</div></div>
    <div class="stat"><div class="val">{report.get('total_contributors', 0)}</div><div class="lbl">Contributors</div></div>
    <div class="stat"><div class="val">{str(report.get('first_commit', ''))[:4]}</div><div class="lbl">Born</div></div>
    <div class="stat"><div class="val">{str(report.get('latest_commit', ''))[:4]}</div><div class="lbl">Last Active</div></div>
  </div>

  <h2>Origin Story</h2>
  {paras(origin)}

  <h2>The Eras</h2>
  {eras_html or '<p>No eras detected.</p>'}

  <h2>The Pivots</h2>
  {pivots_html or '<p>No major pivots detected.</p>'}

  <h2>The Characters</h2>
  {contributors_html or '<p>No contributor profiles generated.</p>'}

  <h2>Ghost Code</h2>
  {ghost_html or '<p>No ghost systems detected.</p>'}

  <h2>Dark Periods</h2>
  {f'<ul>{dark_html}</ul>' if dark_html else '<p>No unusual dark periods detected.</p>'}

  <h2>Present State</h2>
  {paras(present)}

  <h2>The Archeologist\'s Note</h2>
  <blockquote>{note}</blockquote>

  <p class="footer">Generated by Code Archeologist &bull; {str(report.get('analysis_date', ''))[:10]}</p>
</div>
</body>
</html>"""
