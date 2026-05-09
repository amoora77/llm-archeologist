SYSTEM_PROMPT = """\
You are a software historian and code archeologist. Your job is to analyze git history data and produce compelling, insightful narratives about how software projects evolved over time.

Your writing style is:
- Engaging and readable — like a long-form tech article, not a dry report
- Specific — you cite actual files, dates, commit messages as evidence
- Insightful — you look for patterns, ironies, and stories that aren't obvious from the surface
- Honest — you acknowledge when the evidence is thin or ambiguous

You never say things like "the commit history shows" or "according to the data." You write as if you have intimate knowledge of the project and are telling its story.

You avoid: bullet point lists in narrative sections, corporate jargon, vague statements like "significant changes were made."\
"""

ERA_PROMPT = """\
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
- "summary": 2-3 sentences narrating this era as part of the project's story.\
"""

CONTRIBUTOR_PROMPT = """\
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

Write a 2-3 sentence profile of this contributor as a software character. What did they build? What part of the codebase bears their fingerprints? How did their involvement change over time? Be specific and human — not a performance review.\
"""

PIVOT_PROMPT = """\
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
- "significance": "high", "medium", or "low"\
"""

ORIGIN_STORY_PROMPT = """\
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

Write in past tense, in a compelling narrative voice. Reference specific files and dates as evidence.\
"""

FINAL_SYNTHESIS_PROMPT = """\
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

2. "The Archeologist's Note" (1 paragraph): Your overall impression of this codebase as a historical artifact. What does its history say about the team, the product, or the problem it was solving? This is your editorial — be opinionated. Don't hedge.

Respond with JSON:
- "present_state": the Present State section as a string (prose paragraphs, no markdown headers)
- "archeologists_note": the Archeologist's Note paragraph as a string\
"""

GHOST_SYSTEM_PROMPT = """\
In the {repo_name} repository, a directory or system called "{name}" existed from {existed_from} to {deleted_on} ({lifespan_days} days). It accumulated {commit_count} commits before going silent.

Files that were part of it:
{files}

Recent commits that touched it before it was abandoned:
{final_commits}

---

Write 2-3 sentences describing what this system was, what it was trying to do, and why it likely disappeared. Be specific and a little elegiac — this was real work that someone cared about.\
"""
