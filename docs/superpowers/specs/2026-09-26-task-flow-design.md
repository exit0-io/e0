# The whole task flow in the `learning` skill

**Date:** 2026-09-26
**Status:** Implemented
**Source:** `conversation.md` (2026-09-26): the maintainer's description of a regular session,
from orientation through implementation, tests, pull request, review, merge, and questions.

Until now the skill covered the first conversation: install `e0`, open the first issue, walk
the branch. This design covers every session after that. The rules stay the same: `e0` holds
the facts, the skill holds the procedure, and the templates are the lesson.

## The flow

1. **Issue** (open issue = in progress)
2. **Branch** from an updated `main`
3. **Implement**, on the branch
4. **Tests**, run by the student with one command; the result is recorded for `e0 status`
5. **Push and pull request** into `main`; CI runs the same tests
6. **Review** by the agent, against the task's own rules only
7. **Merge and close the issue** (closed issue = complete)
8. **Comprehension questions** on the student's code, recorded as a comment on the issue

## What `e0 status` says now

Every fact the skill needs, so the agent picks a row of a table and never infers.

Per task in progress, `inProgress[]`:

- `checks`: `null` when the catalog says the task has no checks (`"checks": false`), else
  `{"command", "lastRun"}`. `command` is the test command the student runs, built from
  `checks.json`. `lastRun` is `null` until the tests ran, then
  `{"passing", "passed", "failed", "failedTests", "ranAt"}`.
- `pr`: `null` or `{"number", "url", "state", "merged", "branch", "checks", "reviews"}`.
  `checks` is the CI verdict: `"none"`, `"pending"`, `"passing"`, `"failing"`. `reviews`
  counts the Exit0 reviews posted on it (marker `<!-- e0:review -->`).

Per completed task, `completed[]`: the same `pr`, plus `questions`: `null` when the catalog
says the task has none (`"questions": false`), `"done"` when the issue carries the
`<!-- e0:questions -->` comment, else `"pending"`.

`git` gains:

- `branchCommits`: commits on the current branch that `main` does not have (the difference
  between "start" and "keep working").
- `branches`: every local branch with the task in progress its name points at, so the agent
  can suggest `git checkout <branch>` instead of a new branch.

## How the test result is recorded

The student runs the tests themselves; that is part of the learning. `e0` writes a
`conftest.py` next to each task's checks when it downloads them. The hook records
`results.json` in the same folder (`passed`, `failed`, `failedTests`, `ranAt`) and prints one
line at the end of the run, so the student sees what `e0` will see. `e0 check` runs the same
command, so it leaves the same trace. Nothing is stored in `.exit0/state/`.

## New commands

| Command | Does |
|---|---|
| `e0 review <id>` | Hands the agent the PR diff and the rules (`rules.md` of the course and of the task). The rules never touch the disk. |
| `e0 post-review <id> <file>` | Posts the file as a review comment on the PR, with the marker, under the student's identity. |
| `e0 questions <id>` | The task's questions and those of its related topics, decoded (the correct option in `answer`, options shuffled), plus the PR diff to personalize against. |
| `e0 record <id> <file>` | Posts the file as a comment on the task's issue, with the marker. The comprehension check is recorded there and nowhere else. |

## Catalog

Each task entry declares `"checks": true|false` and `"questions": true|false`. `e0` reads
these; it does not guess from what is on disk.

## Knowledge base

The topic `pull-requests` is a convention: the PR template links
`content/knowledge-base/pull-requests.md`, which the agent writes from `e0 read pull-requests`.
A course without the topic gets the same words without the link.

## The skill

`SKILL.md` holds one table, first matching row wins, from Git problems through the fresh
course, the task in progress, the tests, the PR, the review, the merge, and the questions.
Every row links a section of `references/git.md` or the new `references/working.md`, which
holds the templates for the working part of a task. The review and the questions are no
longer "another skill".
