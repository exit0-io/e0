# Curl-Bootstrap Layout Design

**Date:** 2026-08-23
**Status:** Approved
**Supersedes:** `2026-08-20-submodule-layout.md`

---

## Overview

Replace the git-submodule layout with a simple curl-bootstrap approach. The template repo ships
with `.exit0/config.json`. The student says "hi", the agent runs one `curl` command to download
`e0`, then `e0 init` does everything else. No submodules, no extra repos visible in the git tab,
no risk of the agent accidentally editing framework or content files.

---

## Goals

- Student's git tab shows only their own work
- Agent cannot accidentally edit content or framework files (they are never checked out)
- Bootstrap is one `curl` + one `e0 init`
- Canonical task text never lands on disk; agent receives it in the JSON envelope and writes clean marker-free Markdown to `content/`
- Student sees only the files they need: `content/<id>/task.md` and `tests/school-checks/<id>/`
- Only `e0` is versioned; course content always comes from `main`

---

## File Layout

```
<student repo>/
  .exit0/
    e0                    ← CLI (gitignored; downloaded via curl)
    config.json           ← { "courseContentRepo": "exit0-io/demo-content" } (committed)
    catalog.json          ← downloaded by e0 init; gitignored
    skills/               ← downloaded by e0 init; gitignored
      session.md
      working-on-a-task.md
      …                   ← course skills layered on top of framework skills
    state/
      profile.json
      events.jsonl
  content/                ← gitignored; things the student reads
    <task-id>/
      task.md             ← personalized; written by agent after e0 start
    knowledge-base/
      <topic>.md          ← optional; written by agent after e0 read
  tests/
    school-checks/        ← gitignored; downloaded by e0 start
      <task-id>/
        test_greeting.py
        checks.json
    <student's own tests>
```

### `.gitignore` entries added by template

```
.exit0/e0
.exit0/catalog.json
.exit0/skills/
.exit0/state/
content/
tests/school-checks/
```

`.exit0/config.json` is the only `.exit0/` file that is committed.

---

## HTTP Fetch Mechanics

`config.json` carries the GitHub repo slug only:

```json
{ "courseContentRepo": "exit0-io/demo-content" }
```

All URLs are constructed by `e0` at runtime:

| What | URL pattern |
|---|---|
| `catalog.json` | `https://raw.githubusercontent.com/{contentRepo}/main/catalog.json` |
| Task markdown | `https://raw.githubusercontent.com/{contentRepo}/main/tasks/{id}/task.md` |
| Check files | `https://raw.githubusercontent.com/{contentRepo}/main/tasks/{id}/checks/` |
| KB tutorial | `https://raw.githubusercontent.com/{contentRepo}/main/knowledgebase/{topic}/tutorial.md` |
| Framework skills | `https://raw.githubusercontent.com/exit0-io/e0/{E0_VERSION}/cli/skills/{name}.md` |
| Course skills | `https://raw.githubusercontent.com/{contentRepo}/main/skills/{name}.md` |

Course skill filenames are listed in `catalog.json` under `"skills": ["demo-course-notes.md"]`.
Framework skill filenames are hardcoded in `e0` (framework-owned, known at release time).

Content always comes from `main`. Only `e0` is pinned to a release tag.

All fetches use Python `urllib.request` (stdlib only). Network failures return a `problem`
envelope with actionable guidance; they never crash or exit non-zero.

---

## Command Behavior

### `e0 init`

1. Read `.exit0/config.json` → `courseContentRepo`
2. Fetch `catalog.json` from `main` → write `.exit0/catalog.json`
3. Detect OS → write `.exit0/state/profile.json`
4. Fetch framework skills → write `.exit0/skills/`
5. Fetch course skills (names from catalog) → overlay into `.exit0/skills/`
6. Create `.exit0/state/` and `content/` and `tests/school-checks/` directories
7. Append `initialized` event
8. Return `ok` with course title, task count, profile

If catalog fetch fails (no network, wrong repo): return `problem` with guidance to check
`config.json` and internet connection.

### `e0 start <id>`

1. Read `.exit0/catalog.json` → find task
2. Fetch `tasks/{id}/task.md` via HTTP → return as `"canonical"` in JSON envelope
3. Fetch all files listed in `tasks/{id}/checks/checks.json` → write to `tests/school-checks/{id}/`
4. Return `ok` envelope with: `canonical`, `personalization` payload, `checks` paths,
   issue title/body, related topics, dependency warnings

The agent receives the canonical text, personalizes it in memory (selects variant branches,
fills retone blocks), strips all `e0:variant`, `e0:retone`, `when:`, and related HTML comment
markers, and writes clean readable Markdown to `content/{id}/task.md`. It then calls
`e0 verify <id>`.

### `e0 verify <id>`

1. Re-fetch `tasks/{id}/task.md` via HTTP (canonical, has markers)
2. Read `content/{id}/task.md` (personalized, marker-free clean Markdown)
3. Extract all **fixed** text chunks from the canonical (text outside `e0:variant` and `e0:retone` blocks)
4. Check each fixed chunk appears verbatim in the personalized file
5. If any fixed chunk is missing or altered: return `problem` listing violations (no restore — the
   file is clean Markdown; the agent re-personalizes if needed)
6. If all fixed chunks present: return `ok`

No canonical is cached to disk. The extra HTTP request is acceptable.
The current marker-alignment verify algorithm is replaced by this fixed-chunk approach.

### `e0 read <topic>`

1. Fetch `knowledgebase/{topic}/tutorial.md` via HTTP
2. Return tutorial text in JSON envelope as `"tutorial"`

The agent presents the tutorial in chat and optionally writes to
`content/knowledge-base/{topic}.md` if the student wants a persistent copy.

### `e0 status` / `e0 catalog`

Read from `.exit0/catalog.json` + `state/events.jsonl` — no network call.

### `e0 check` *(deferred)*

Downloaded check files land in `tests/school-checks/{id}/`. The UX for running them is
a separate feature.

---

## AGENTS.md (template)

```markdown
<!-- =================================================================
     EXIT ZERO — DO NOT MODIFY THIS SECTION
     ================================================================= -->

## Course setup

If `.exit0/e0` missing:
```bash
RELEASE=v1.0
curl -fsSL "https://raw.githubusercontent.com/exit0-io/e0/${RELEASE}/cli/bin/e0" -o .exit0/e0 && chmod +x .exit0/e0
.exit0/e0 init
```
After init: tell the student to allow `.exit0/e0` to run without confirmation — it drives the course, sends no personal info anywhere.

## Info

- Every session: Read `.exit0/skills/session.md` before anything else.

- Learning cycle: Tasks → GitHub issues. `e0 read <topic>` for knowledge base. Feature branch → PR → review → comp check → close PR = done.

- Course questions: `.exit0/catalog.json` has everything: tasks, topics, technologies, order.

- Skills: All in `.exit0/skills/`. Session skill loads them.

<!-- ================================================================= END EXIT ZERO ================================================================= -->
```

## Changes from Submodule Layout

| Was | Now |
|---|---|
| `.exit0/e0/` submodule | `.exit0/e0` single file, curl-downloaded |
| `.exit0/content/` submodule | No checkout; content fetched on demand |
| `exit0.json` | `.exit0/config.json` |
| `state_dir` → `.exit0/e0/state/` | `state_dir` → `.exit0/state/` |
| `content_dir` → `.exit0/content/` | Content fetched, never stored (except `catalog.json`) |
| `task.canonical.md` cached on disk | Canonical re-fetched at verify time |
| `tests/` not prescribed | `tests/school-checks/{id}/` for downloaded checks |
| Student sees 2 extra repos in git tab | Student sees only their own repo |

---

## What Is Not Changing

- Single-file Python 3, stdlib only, never crashes, always exits 0
- JSON envelope shape (`ok`/`problem` with `command`, `data`, `message`, `guidance`)
- Personalization contract: `e0:variant` and `e0:retone` markers guide the agent; final file is clean Markdown; `e0 verify` checks fixed regions are intact
- Progress / sync / `e0 complete` — unchanged
- `e0 feedback`, `e0 profile`, `e0 questions`, `e0 answer` — unchanged
