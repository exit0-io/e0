I DELETED THE PLAN CONTENT BECAUSE I MADE A LOT OF CHANGES AND IT'S HARD TO KEEP TRACK OF WHAT'S NEW. I UPDATED ONLY THE SPEC.

## What This Plan Deliberately Leaves Out

These are specified in the design and belong to later plans. They are listed so a reviewer
does not mistake their absence for an oversight:

| Deferred | Plan |
|---|---|
| `e0 review`, `e0 pr-comment` — PR review and conduct rules | 2 |
| `e0 questions`, `e0 answer`, `e0 complete` — comprehension checks, spaced repetition | 2 |
| Enforcing that question ids equal `sha1(prompt)[:8]` — fixture ids are opaque placeholders until questions are actually consumed | 2 |
| `e0 sync` — orphan-branch progress commits | 3 |
| `e0 update` — migrations and version changes | 3 |
| `e0 read` — real knowledge base fetch and personalization, replacing the Task 12 stub | 3 |
| `e0 feedback` — feedback issues | 4 |
| The minimal backend — `/issue`, `/progress`, `/webhook` | Later |

Two things that look like gaps but are not:

- **CI wiring is course content, not platform work.** The spec has the student build the GitHub
  Actions workflow themselves as an early task. `e0 check` and that workflow run the same files
  from `checks.json`, so nothing here needs to change when it lands.
- **There is no separate demo content directory.** The demo course's content *is*
  `e0/tests/fixtures/course/`, which keeps one miniature course rather than two copies that
  drift. Published, it becomes `exit0/demo-content`; `agent-native/courses/demo/template/`
  becomes `exit0/demo-template`.
