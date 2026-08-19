# Exit Zero

An agent-native learning **framework**. It hosts courses; it is not one.

| Directory | Becomes | Contents |
|---|---|---|
| `e0/` | `exit0/e0` | The framework: the CLI and the skills that drive it. Course-agnostic. |
| `courses/demo/template/` | `exit0/demo-template` | What a student of the demo course forks |
| `e0/tests/fixtures/course/` | `exit0/demo-content` | The demo course's content, doubling as the test fixture |

A course is a content repo plus a template repo. The template names its course in `exit0.json`,
which is how a course-agnostic framework learns what it is running. Adding a course requires no
change to `e0`; fixing `e0` requires republishing no course.

Nothing outside this directory is part of this work. `services/`, `projects/`, and
`pr-evaluation-action/` belong to the earlier frontend-native approach and are untouched.

Design spec: `docs/superpowers/specs/2026-08-09-agent-native-learning-design.md`

## Running the tests

```bash
cd agent-native/e0 && python -m pytest -v
```

## Commands implemented so far

| Command | Purpose |
|---|---|
| `e0 init` | Fetch pinned content, detect the environment, scaffold `.exit0/` |
| `e0 status` | Where the student is, what is next, whether an update exists |
| `e0 catalog` | Every task with dependencies and status |
| `e0 start <id>` | Materialize a task with its checks and personalization payload |
| `e0 verify <id>` | Enforce the personalization contract, restoring violations |
| `e0 check [id]` | Run the task's school checks, warning on drift |
| `e0 profile get\|set` | Read or record a detected fact |
| `e0 help` | List commands |

Still to come, in later plans: `review`, `pr-comment`, `questions`, `answer`, `complete`,
`read`, `sync`, `update`, `feedback`.

