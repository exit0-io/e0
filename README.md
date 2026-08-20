# Exit Zero

An agent-native learning framework. 

A student starting a software engineering course by forking a course template, then works through it with their coding agent (just send **hi** in the chat panel). The agent fetches the course technical content, instructs the student task by task, runs tests or students' code, reviews PRs, and asks the student questions on its implementation. 


## Running tests

```bash
cd e0 && python -m pytest -v
```

With coverage:

```bash
COVERAGE_PROCESS_START=/path/to/cli/setup.cfg python -m coverage run --rcfile=setup.cfg -m pytest -q
python -m coverage combine --rcfile=setup.cfg && python -m coverage report --rcfile=setup.cfg --include="bin/e0"
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

