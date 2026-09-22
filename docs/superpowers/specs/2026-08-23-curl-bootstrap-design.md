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

### Progress lives in GitHub issues *(revised 2026-09-16)*

`e0` keeps no progress of its own. There is no event log. The student's progress is the set of
GitHub issues in their repo: an open issue titled `[T010] ...` means T010 is in progress, a
closed one means it is complete. `e0` reads them with `gh issue list --state all --json ...`.
If `gh` is missing or logged out, `status`, `catalog`, and `start` return a `problem` with
guidance; `task` still works and reports progress as `unknown` with a warning.

The only local state is `.exit0/state/profile.json`.

### `e0 task <id>` *(revised 2026-09-16)*

Fetch a task for the agent. It starts nothing, so the agent can run it when the student only
asks what a task is about, and again when they ask to start.

1. Read `.exit0/catalog.json` → find task
2. Fetch `tasks/{id}/task.md` via HTTP → return as `canonical` (has markers)
3. Fetch all files listed in `tasks/{id}/checks/checks.json` → write to `tests/school-checks/{id}/`
4. Return: `task` (the full catalog entry, every author field passed through), `canonical`,
   `personalization` (variants, retone blocks, facts), `paths`, `status`, `unmetDependencies`,
   `warnings`

The agent personalizes exactly as the personalization contract says (select one variant branch
per `facts`, fill retone blocks only from what the student said, change nothing else, strip the
markers) and writes clean Markdown to `content/{id}/task.md`. It does this silently: the step is
part of the framework, not something the student is told about.

### `e0 start <id>` *(revised 2026-09-16)*

1. Read progress from GitHub. Refuse with a `problem` if the task already has an issue (open:
   in progress; closed: complete)
2. Refuse with a `problem` if `content/{id}/task.md` does not exist (guidance: run `e0 task`)
3. Re-fetch the canonical and verify the file. Violations are a `problem`; no issue is returned
4. Unmet dependencies add a `dependency` warning
5. Return `task`, `paths`, `warnings`, and `issue`: `title` is `[<id>] <title>`, `body` is the
   **whole personalized task text**. The agent opens the issue; that open issue is the record.

### `e0 verify <id>`

1. Re-fetch `tasks/{id}/task.md` via HTTP (canonical, has markers)
2. Read `content/{id}/task.md` (clean Markdown, possibly with an agent note)
3. Extract all **fixed** text chunks from the canonical (text outside `e0:variant` and `e0:retone` blocks)
4. Check each fixed chunk appears verbatim in the file
5. If any fixed chunk is missing or altered: return `problem` listing violations. Guidance:
   personalize again from `data.canonical` of `e0 task <id>`
6. If all fixed chunks present: return a success

`e0 start` runs the same check before it returns the issue.

No canonical is cached to disk. The extra HTTP request is acceptable.

### `e0 read <topic>`

1. Fetch `knowledgebase/{topic}/tutorial.md` via HTTP
2. Return tutorial text in JSON envelope as `"tutorial"`

The agent presents the tutorial in chat and optionally writes to
`content/knowledge-base/{topic}.md` if the student wants a persistent copy.

### `e0 status` / `e0 catalog`

Read from `.exit0/catalog.json` + the repo's GitHub issues (via `gh`). No content fetch.

`status` returns three lists, because tasks form a tree and more than one can be ready at once:
`inProgress`, `next` (not started, every dependency complete), `completed`. It carries no
procedure text; procedure lives in the `learning` skill.

`catalog` passes every task's catalog entry through untouched, plus `status`. New author fields
(purpose, learning goals, ...) reach the agent with no change to `e0`.

### Envelope *(revised 2026-09-16)*

A success is `{"command", "data", "message"}`. A failure is
`{"command", "problem", "guidance", "message"}` (plus `data` where there is detail, such as
`verify` violations or `check` output). There is no `ok` boolean: the presence of `problem` is
the signal.

### Bootstrap and releases *(added 2026-09-16)*

The skill pins `RELEASE=<E0_VERSION>` and downloads
`raw.githubusercontent.com/exit0-io/e0/<tag>/cli/bin/e0`. If that fails, it falls back to
`github.com/exit0-io/e0/releases/latest/download/e0`. The `Release e0` GitHub Actions workflow
creates the tag and the release, with `e0` as an asset, on every push to `main` that changes
`cli/bin/e0` and introduces a new `E0_VERSION`. `e0 init` fetches its skills from the pinned tag
and falls back to `main` if the tag is not published.

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
- Personalization contract: `e0:variant` and `e0:retone` markers guide the agent; the agent writes the final clean Markdown; `e0 verify` (and `e0 start`) check fixed regions are intact
- Progress / sync / `e0 complete` — unchanged
- `e0 feedback`, `e0 profile`, `e0 questions`, `e0 answer` — unchanged
