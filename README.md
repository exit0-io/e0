# Exit0

An agent-native learning framework.

A student starts a software engineering course by forking a course template, then works through it with their coding agent (just send **hi** in the chat panel). The agent fetches the course technical content, instructs the student task by task, runs tests or students' code, reviews PRs, and asks the student questions on its implementation.

## Running tests

```bash
cd cli && ../.venv/bin/python -m pytest -v
```

Agent evals run the real coding agent (cheapest model) against a fixture course repo and check
what it says and does. They cost money, so they are opt-in:

```bash
cd cli && E0_AGENT_EVALS=1 ../.venv/bin/python -m pytest tests/test_agent_evals.py -v
```

Scenarios live in `cli/tests/evals/`. Each one records the transcript comment it came from.

With coverage:

```bash
COVERAGE_PROCESS_START=/path/to/cli/setup.cfg python -m coverage run --rcfile=setup.cfg -m pytest -q
python -m coverage combine --rcfile=setup.cfg && python -m coverage report --rcfile=setup.cfg --include="bin/e0"
```

## Releasing

Bump `E0_VERSION` in `cli/bin/e0` and `RELEASE=` in `cli/skills/learning/references/setup-and-update.md` to the same tag. When the change lands on `main`, the `Release e0` GitHub Actions workflow creates the tag and the release, and uploads `e0` as a release asset. The skill downloads the pinned tag and falls back to `releases/latest/download/e0`.

## Where progress lives

In the student's GitHub issues and pull requests, nowhere else. An open issue titled `[T010] ...` is a task in progress. A closed one is complete. A PR is linked to a task by `[T010]` in its title or the issue number in its body. `e0 status` flags a closed issue with no merged PR, so the agent can say a step was skipped. `e0` reads all this with `gh`, so the student needs the GitHub CLI installed and logged in. The only local state is `.exit0/state/profile.json`.

## Output shape

Every command prints one JSON object and exits 0. A reply that worked has `command`, `data`, `message`. A reply that failed has `command`, `problem`, `guidance`, `message`. The presence of `problem` is the signal; there is no boolean flag.

## Commands implemented so far

| Command | Purpose |
|---|---|
| `e0 init` | Fetch the catalog and skills, detect the machine, scaffold `.exit0/` |
| `e0 status` | Tasks in progress, ready to start (a list: tasks form a tree), and completed. Read from the repo's GitHub issues via `gh` |
| `e0 catalog` | Every task with its full catalog entry and status |
| `e0 task <id>` | Fetch a task: the canonical text and personalization payload for the agent, plus its checks. Starts nothing |
| `e0 start <id>` | Verify the agent's `content/<id>/task.md` and return the GitHub issue (title + full task text). The open issue marks the task in progress |
| `e0 verify <id>` | Check that `content/<id>/task.md` still carries every protected part of the original |
| `e0 check [id]` | Run the task's school checks, warning on drift |
| `e0 read [topic]` | List knowledge base topics, or fetch one tutorial |
| `e0 profile get\|set` | Read or record a fact about the student's machine |
| `e0 help` | List commands |

Still to come, in later plans: `review`, `pr-comment`, `questions`, `answer`, `complete`,
`sync`, `update`, `feedback`.
