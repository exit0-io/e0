# Exit Zero Framework — Walking Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A student can fork a course's template repo, say "hi" to their coding agent, and end up working on task 1 — personalized to their machine, with runnable tests on disk — with no backend, no auth, and no frontend.

**Architecture:** Exit Zero is a course-agnostic **framework**. Its CLI (`e0`) holds all deterministic logic: environment detection, content fetch, dependency lookup, personalization verification, and check execution. The framework ships `e0` plus the skills that describe how to use it. Each **course** it hosts is a separate content repo (tasks, tutorials, question banks, checks) plus a template repo students fork; the template names its course in `exit0.json`. All student state lives under gitignored `.exit0/`.

**Tech Stack:** Python 3.9+ (standard library only at runtime), git (invoked as a subprocess), pytest (development only).

## Terminology

Used precisely throughout this plan. Getting these wrong produces the wrong file layout.

| Term | Means |
|---|---|
| **Exit Zero** (`exit0`) | The learning framework. Course-agnostic. |
| **`e0`** | The framework's CLI. One implementation, serving every course. |
| **Course** | Something the framework hosts — `polybot`, `polyAIdev`, `MIT2026AIBootcamp`. |
| **Framework repo** | `exit0/e0` — the CLI and its skills. Released independently of any course. |
| **Course content repo** | `exit0/<course-content-repo>` — catalog, tasks, tutorials, question banks, checks. |
| **Course template repo** | `exit0/<course-template-repo>` — what a student forks. One per course. |

Repository names are free. A course called `MIT2026AIBootcamp` might have a template repo named
`PolyAIMIT`; nothing parses either name. The course's identity is `course.id` in `catalog.json`,
and a fork reaches its content through the full URL in `exit0.json`. The demo course in this
plan happens to use `demo-content` and `demo-template` — chosen names, not a required pattern.

## Global Constraints

- `e0` is **one file**, `agent-native/e0/bin/e0`, with no extension and a `#!/usr/bin/env python3` shebang. It is the framework's only executable and must run standalone.
- **Runtime dependencies: Python 3.9+ standard library only.** No third-party imports in `e0`. `pytest` is a development dependency of the test suite, never of the CLI.
- **`e0` never crashes.** Every invocation exits `0` and prints one JSON object to stdout. No stack traces, no non-zero exits, no unhandled exceptions. This is the load-bearing guarantee of the whole design and is tested explicitly.
- Every command's output is the envelope defined in Task 1. Success and failure differ by the `ok` field, never by exit code.
- **The framework knows nothing about any specific course.** No course id, task id, or topic name may appear in `e0` or in a framework skill. Course-specific knowledge lives only in a course content repo. A test enforces this.
- **No network access in tests.** Content fetch is tested against local git repositories created in temp directories. The course content repo URL comes from `E0_CONTENT_REPO` when set, and the framework directory from `E0_FRAMEWORK_DIR`.
- All new code lives under `agent-native/`. **Nothing outside `agent-native/` is created, modified, or deleted** — `services/`, `projects/`, `infra/`, and `pr-evaluation-action/` belong to the previous frontend-native approach and are left exactly as they are.
- Content is GitHub-flavored Markdown. It must render correctly in VS Code's Markdown preview, on github.com, and in a chat transcript.
- Commit after every task. Use conventional commit prefixes (`feat:`, `test:`, `chore:`, `docs:`).

## Deviation From The Spec (flagged)

The spec illustrates variant branches with trailing comments:

```markdown
brew install ffmpeg          <!-- when: os=macos -->
```

A trailing comment cannot introduce a fenced code block, and install instructions usually are one. This plan uses a **leading** marker instead, which is semantically identical and supports multi-line branches:

```markdown
<!-- when: os=macos -->
```bash
brew install ffmpeg
```
```

Everything else follows the spec as written.

## File Structure

| Path | Responsibility |
|---|---|
| `agent-native/README.md` | What this directory is and how framework and courses relate |
| `agent-native/e0/bin/e0` | The framework CLI — every deterministic operation |
| `agent-native/e0/skills/` | Framework skills — procedure, course-agnostic |
| `agent-native/e0/pytest.ini` | Test configuration |
| `agent-native/e0/tests/conftest.py` | Loads `e0` as a module; builds fixture course repos and student repos |
| `agent-native/e0/tests/fixtures/course/` | A complete miniature course, used by every test and doubling as the content schema reference |
| `agent-native/e0/tests/test_*.py` | One test module per command |
| `agent-native/courses/demo/template/` | Seed of the demo course's template repo |

The framework repo is `agent-native/e0/`; published, it becomes `exit0/e0`. Each course lives
under `agent-native/courses/<course>/`. The demo course's content is the test fixture rather than
a second copy — there is one miniature course, and the tests are its consumer.

Within `e0`, code is organized in labeled sections in this order: envelope helpers, process/git helpers, repo and path discovery, state (events and profile), course fetch, marker parsing, command handlers, dispatch table, `main`. Later tasks append their handler to the command section and register it in the dispatch table.

---

### Task 1: Scaffold, Result Envelope, and the Never-Crash Harness

**Files:**
- Create: `agent-native/README.md`
- Create: `agent-native/e0/bin/e0`
- Create: `agent-native/e0/pytest.ini`
- Create: `agent-native/e0/tests/conftest.py`
- Create: `agent-native/e0/tests/test_harness.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `ok(command: str, data: dict = None, message: str = "") -> dict`
  - `problem(command: str, problem: str, guidance: str, message: str = None) -> dict`
  - `COMMANDS: dict[str, Callable[[list[str]], dict]]`
  - `main(argv: list[str] = None) -> int` — always returns `0`
  - conftest fixtures: `e0mod` (the loaded module), `run_e0(args, cwd, env=None) -> dict`

- [ ] **Step 1: Create the directory README**

Create `agent-native/README.md`:

```markdown
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
```

- [ ] **Step 2: Create `pytest.ini`**

Create `agent-native/e0/pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 3: Write the conftest that loads `e0` as a module**

Create `agent-native/e0/tests/conftest.py`:

```python
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import subprocess
import sys

import pytest

E0_PATH = pathlib.Path(__file__).resolve().parent.parent / "bin" / "e0"


def _load_e0():
    loader = importlib.machinery.SourceFileLoader("e0", str(E0_PATH))
    spec = importlib.util.spec_from_loader("e0", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@pytest.fixture
def e0mod():
    return _load_e0()


@pytest.fixture
def run_e0():
    """Invoke e0 as a real subprocess and return (parsed_json, exit_code)."""

    def _run(args, cwd, env=None):
        merged = dict(os.environ)
        merged.update(env or {})
        proc = subprocess.run(
            [sys.executable, str(E0_PATH), *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            env=merged,
        )
        payload = json.loads(proc.stdout)
        return payload, proc.returncode

    return _run
```

- [ ] **Step 4: Write the failing tests**

Create `agent-native/e0/tests/test_harness.py`:

```python
def test_ok_envelope_shape(e0mod):
    result = e0mod.ok("status", {"a": 1}, "all good")
    assert result == {
        "ok": True,
        "command": "status",
        "data": {"a": 1},
        "message": "all good",
    }


def test_problem_envelope_shape(e0mod):
    result = e0mod.problem("start", "Task not found.", "Run 'e0 catalog'.")
    assert result["ok"] is False
    assert result["command"] == "start"
    assert result["problem"] == "Task not found."
    assert result["guidance"] == "Run 'e0 catalog'."
    assert "Task not found." in result["message"]
    assert "Run 'e0 catalog'." in result["message"]


def test_unknown_command_is_a_problem_not_a_crash(run_e0, tmp_path):
    payload, code = run_e0(["definitely-not-a-command"], tmp_path)
    assert code == 0
    assert payload["ok"] is False
    assert "definitely-not-a-command" in payload["problem"]


def test_no_arguments_is_not_a_crash(run_e0, tmp_path):
    payload, code = run_e0([], tmp_path)
    assert code == 0
    assert isinstance(payload["ok"], bool)


def test_handler_exception_is_caught_and_reported(e0mod, capsys):
    def exploding_handler(args):
        raise RuntimeError("boom")

    e0mod.COMMANDS["explode"] = exploding_handler
    code = e0mod.main(["explode"])
    captured = capsys.readouterr()
    payload = __import__("json").loads(captured.out)

    assert code == 0
    assert payload["ok"] is False
    assert "RuntimeError" in payload["problem"]
    assert "boom" in payload["problem"]


def test_help_lists_every_registered_command(run_e0, tmp_path, e0mod):
    payload, code = run_e0(["help"], tmp_path)
    assert code == 0
    assert payload["ok"] is True
    for name in e0mod.COMMANDS:
        assert name in payload["data"]["commands"]
```

- [ ] **Step 5: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: collection error — `FileNotFoundError` for the `e0` file, since it does not exist yet.

- [ ] **Step 6: Implement `e0`**

Create `agent-native/e0/bin/e0` with this content:

```python
#!/usr/bin/env python3
"""e0 — the Exit Zero framework CLI.

Exit Zero hosts courses; this CLI knows nothing about any of them. Single file,
standard library only. Never crashes: every invocation exits 0 and prints exactly
one JSON object to stdout.
"""

import json
import sys

E0_VERSION = "1.0"

# ---------------------------------------------------------------- envelope


def ok(command, data=None, message=""):
    return {
        "ok": True,
        "command": command,
        "data": data if data is not None else {},
        "message": message,
    }


def problem(command, problem, guidance, message=None):
    return {
        "ok": False,
        "command": command,
        "problem": problem,
        "guidance": guidance,
        "message": message if message is not None else f"{problem} {guidance}",
    }


# ---------------------------------------------------------------- commands


def cmd_help(args):
    return ok(
        "help",
        {"commands": sorted(COMMANDS)},
        "Available commands: " + ", ".join(sorted(COMMANDS)),
    )


# ---------------------------------------------------------------- dispatch

COMMANDS = {
    "help": cmd_help,
}

DEFAULT_COMMAND = "help"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    command = argv[0] if argv else DEFAULT_COMMAND
    rest = argv[1:]

    try:
        handler = COMMANDS.get(command)
        if handler is None:
            result = problem(
                command,
                f"Unknown command '{command}'.",
                "Run 'e0 help' to see what is available.",
            )
        else:
            result = handler(rest)
    except Exception as exc:  # noqa: BLE001 - the never-crash guarantee lives here
        result = problem(
            command,
            f"e0 hit an unexpected error: {exc.__class__.__name__}: {exc}",
            "This is a bug in e0. Re-running usually will not help; "
            "please report it with this message.",
        )

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 7: Make `e0` executable**

Run: `chmod +x agent-native/e0/bin/e0`

- [ ] **Step 8: Run the tests to verify they pass**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: 6 passed.

- [ ] **Step 9: Commit**

```bash
git add agent-native/
git commit -m "feat(e0): scaffold, result envelope, never-crash harness"
```

---

### Task 2: Fixture Course Content

A complete miniature course. Every later task tests against it, and it doubles as the reference for the content schema.

**Files:**
- Create: `agent-native/e0/tests/fixtures/course/catalog.json`
- Create: `agent-native/e0/tests/fixtures/course/rules.md`
- Create: `agent-native/e0/tests/fixtures/course/knowledgebase/index.json`
- Create: `agent-native/e0/tests/fixtures/course/knowledgebase/intro-to-linux/tutorial.md`
- Create: `agent-native/e0/tests/fixtures/course/knowledgebase/intro-to-linux/questions.json`
- Create: `agent-native/e0/tests/fixtures/course/tasks/t010/task.md`
- Create: `agent-native/e0/tests/fixtures/course/tasks/t010/rules.md`
- Create: `agent-native/e0/tests/fixtures/course/tasks/t010/questions.json`
- Create: `agent-native/e0/tests/fixtures/course/tasks/t010/checks/checks.json`
- Create: `agent-native/e0/tests/fixtures/course/tasks/t010/checks/test_greeting.py`
- Create: `agent-native/e0/tests/fixtures/course/tasks/t020/task.md`
- Create: `agent-native/e0/tests/fixtures/course/tasks/t020/checks/checks.json`
- Create: `agent-native/e0/tests/fixtures/course/tasks/t020/checks/test_farewell.py`
- Modify: `agent-native/e0/tests/conftest.py`
- Create: `agent-native/e0/tests/test_fixtures.py`

**Interfaces:**
- Consumes: `conftest` from Task 1
- Produces:
  - `content_repo` fixture → `pathlib.Path` to a git repo containing the fixture course, tagged `v0.1.0`
  - `make_course_repo` factory fixture → builds a course repo, optionally mutating its catalog first
  - `framework_dir` fixture → `pathlib.Path` to `agent-native/e0`, which has the same shape as `.exit0/framework/`
  - `student_repo` fixture → `pathlib.Path` to an initialized git repo with one commit, standing in for the student's fork

- [ ] **Step 1: Create the catalog**

Create `agent-native/e0/tests/fixtures/course/catalog.json`:

```json
{
  "contentTag": "v0.1.0",
  "requiresE0": "1.0",
  "course": {
    "id": "demo",
    "title": "Demo Course",
    "feedbackRepo": "exit0/feedback"
  },
  "tasks": [
    {
      "id": "T010",
      "title": "Say hello",
      "description": "Write a greeting function.",
      "labels": ["Python"],
      "dependsOn": [],
      "order": 1,
      "relatedTopics": ["intro-to-linux"]
    },
    {
      "id": "T020",
      "title": "Say goodbye",
      "description": "Write a farewell function.",
      "labels": ["Python"],
      "dependsOn": ["T010"],
      "order": 2,
      "relatedTopics": []
    }
  ]
}
```

- [ ] **Step 2: Create the course-wide rules**

Create `agent-native/e0/tests/fixtures/course/rules.md`:

```markdown
# Conduct rules

- Do not close a pull request before it has been reviewed.
- Do not commit files unrelated to the task.
```

- [ ] **Step 3: Create the knowledge base**

Create `agent-native/e0/tests/fixtures/course/knowledgebase/index.json`:

```json
{
  "topics": [
    {
      "id": "intro-to-linux",
      "title": "Intro to Linux",
      "topics": ["shell", "pipes", "permissions"],
      "summary": "Navigating a shell, chaining commands with pipes, and reading file permissions."
    }
  ]
}
```

Create `agent-native/e0/tests/fixtures/course/knowledgebase/intro-to-linux/tutorial.md`:

```markdown
# Intro to Linux

The shell is how you talk to the operating system.

## Pipes

The `|` character sends the output of one command into the input of the next.

```bash
cat access.log | grep ERROR | wc -l
```
```

Create `agent-native/e0/tests/fixtures/course/knowledgebase/intro-to-linux/questions.json`:

```json
{
  "questions": [
    {
      "id": "b1d4e7a2",
      "topic": "pipes",
      "type": "mcq",
      "prompt": "What does the | character do in a shell command?",
      "options": [
        "Sends one command's output into the next command's input",
        "Runs two commands at the same time",
        "Comments out the rest of the line",
        "Redirects output into a file"
      ],
      "answerHash": "REPLACED_IN_STEP_7",
      "reaskAfterDays": 30
    }
  ]
}
```

- [ ] **Step 4: Create task T010**

Create `agent-native/e0/tests/fixtures/course/tasks/t010/task.md`:

````markdown
# Say hello

## Related Topics

- Intro to Linux

## Setup

<!-- e0:variant id="run-tests" -->
<!-- when: os=linux -->
```bash
python3 -m pytest .exit0/tasks/t010/checks -v
```
<!-- when: os=macos -->
```bash
python3 -m pytest .exit0/tasks/t010/checks -v
```
<!-- when: os=windows -->
```powershell
py -m pytest .exit0\tasks\t010\checks -v
```
<!-- /e0:variant -->

<!-- e0:retone based-on="the student's Python experience" -->
<!-- /e0:retone -->

## Task

Create `greeting.py` in the repository root with a function `greet(name)` that returns
`Hello, <name>!`.

Build it using the **standard library** only.
````

Create `agent-native/e0/tests/fixtures/course/tasks/t010/rules.md`:

```markdown
- The greeting must be produced by a function, not printed at module level.
```

Create `agent-native/e0/tests/fixtures/course/tasks/t010/questions.json`:

```json
{
  "questions": [
    {
      "id": "c9f01a55",
      "topic": "python",
      "type": "mcq",
      "prompt": "What does a Python function return when it has no return statement?",
      "options": ["None", "An empty string", "0", "It raises an error"],
      "answerHash": "REPLACED_IN_STEP_7",
      "reaskAfterDays": 30
    },
    {
      "id": "d3b7c018",
      "topic": "python",
      "type": "open",
      "prompt": "Why does greet() return a value instead of printing it?",
      "openAnswerOutline": "Returning lets the caller decide what to do with the value; printing couples the function to one output channel and makes it hard to test.",
      "mandatory": true
    }
  ]
}
```

Create `agent-native/e0/tests/fixtures/course/tasks/t010/checks/checks.json`:

```json
{
  "run": ["python3", "-m", "pytest", "{checks_dir}", "-v"],
  "files": {
    "test_greeting.py": "REPLACED_IN_STEP_7"
  }
}
```

Create `agent-native/e0/tests/fixtures/course/tasks/t010/checks/test_greeting.py`:

```python
# Exit Zero school check. Do not edit this file.
# Your local copy is only for running tests while you work; CI uses the original.

import os
import sys

# e0 runs checks from the repository root.
sys.path.insert(0, os.getcwd())


def test_greet_returns_expected_string():
    import greeting

    assert greeting.greet("Ada") == "Hello, Ada!"
```

- [ ] **Step 5: Create task T020**

Create `agent-native/e0/tests/fixtures/course/tasks/t020/task.md`:

```markdown
# Say goodbye

## Task

Add a function `farewell(name)` to `greeting.py` that returns `Goodbye, <name>!`.
```

Create `agent-native/e0/tests/fixtures/course/tasks/t020/checks/checks.json`:

```json
{
  "run": ["python3", "-m", "pytest", "{checks_dir}", "-v"],
  "files": {
    "test_farewell.py": "REPLACED_IN_STEP_7"
  }
}
```

Create `agent-native/e0/tests/fixtures/course/tasks/t020/checks/test_farewell.py`:

```python
# Exit Zero school check. Do not edit this file.

import os
import sys

# e0 runs checks from the repository root.
sys.path.insert(0, os.getcwd())


def test_farewell_returns_expected_string():
    import greeting

    assert greeting.farewell("Ada") == "Goodbye, Ada!"
```

- [ ] **Step 6: Add the repo-building fixtures to conftest**

Append to `agent-native/e0/tests/conftest.py`:

```python
FIXTURE_COURSE = pathlib.Path(__file__).resolve().parent / "fixtures" / "course"
FRAMEWORK_DIR = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture
def framework_dir():
    """In development, agent-native/e0/ has the same shape as .exit0/framework/."""
    return FRAMEWORK_DIR


def _git(cwd, *args):
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.com",
            "GIT_COMMITTER_NAME": "Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.com",
        },
    )


@pytest.fixture
def make_course_repo(tmp_path):
    """Build a course content repo, optionally mutating its catalog first."""
    import shutil

    counter = {"n": 0}

    def _make(mutate_catalog=None):
        counter["n"] += 1
        repo = tmp_path / f"course-repo-{counter['n']}"
        shutil.copytree(FIXTURE_COURSE, repo)
        if mutate_catalog is not None:
            catalog_path = repo / "catalog.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            mutate_catalog(catalog)
            catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
        _git(repo, "init", "-q", "-b", "main")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "fixture course")
        _git(repo, "tag", "v0.1.0")
        return repo

    return _make


@pytest.fixture
def content_repo(make_course_repo):
    """A git repo holding the fixture course, tagged v0.1.0."""
    return make_course_repo()


@pytest.fixture
def student_repo(tmp_path):
    """An initialized git repo standing in for the student's fork."""
    repo = tmp_path / "student-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# My course work\n", encoding="utf-8")
    (repo / "exit0.json").write_text(
        json.dumps({"courseRepo": "https://example.invalid/unused.git"}, indent=2),
        encoding="utf-8",
    )
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "initial")
    return repo
```

- [ ] **Step 7: Write a test that fills in the placeholder hashes**

Create `agent-native/e0/tests/test_fixtures.py`:

```python
import hashlib
import json
import pathlib

FIXTURE_COURSE = pathlib.Path(__file__).resolve().parent / "fixtures" / "course"


def test_no_placeholder_hashes_remain():
    """Every answerHash and check file hash must be a real sha256."""
    offenders = []
    for path in FIXTURE_COURSE.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        if "REPLACED_IN_STEP_7" in text:
            offenders.append(str(path.relative_to(FIXTURE_COURSE)))
    assert offenders == [], f"placeholder hashes left in: {offenders}"


def test_answer_hashes_match_exactly_one_option():
    for path in FIXTURE_COURSE.rglob("questions.json"):
        bank = json.loads(path.read_text(encoding="utf-8"))
        for question in bank["questions"]:
            if question["type"] != "mcq":
                continue
            matches = [
                option
                for option in question["options"]
                if hashlib.sha256(option.encode("utf-8")).hexdigest()
                == question["answerHash"]
            ]
            assert len(matches) == 1, (
                f"{path.name} question {question['id']} must have exactly one "
                f"correct option, found {len(matches)}"
            )


def test_check_file_hashes_match_the_files_on_disk():
    for checks_json in FIXTURE_COURSE.rglob("checks/checks.json"):
        spec = json.loads(checks_json.read_text(encoding="utf-8"))
        for name, expected in spec["files"].items():
            actual = hashlib.sha256(
                (checks_json.parent / name).read_bytes()
            ).hexdigest()
            assert actual == expected, f"{name} hash is stale"


def test_every_dependson_and_relatedtopic_resolves():
    catalog = json.loads((FIXTURE_COURSE / "catalog.json").read_text(encoding="utf-8"))
    index = json.loads(
        (FIXTURE_COURSE / "knowledgebase" / "index.json").read_text(encoding="utf-8")
    )
    task_ids = {task["id"] for task in catalog["tasks"]}
    topic_ids = {topic["id"] for topic in index["topics"]}

    for task in catalog["tasks"]:
        for dependency in task["dependsOn"]:
            assert dependency in task_ids, f"{task['id']} depends on unknown {dependency}"
        for topic in task["relatedTopics"]:
            assert topic in topic_ids, f"{task['id']} references unknown topic {topic}"


def test_every_task_directory_has_checks():
    catalog = json.loads((FIXTURE_COURSE / "catalog.json").read_text(encoding="utf-8"))
    for task in catalog["tasks"]:
        checks = FIXTURE_COURSE / "tasks" / task["id"].lower() / "checks" / "checks.json"
        assert checks.exists(), f"{task['id']} has no checks.json"


def test_catalog_declares_its_framework_requirement():
    """A course must state the minimum e0 it needs; the framework ships separately."""
    catalog = json.loads((FIXTURE_COURSE / "catalog.json").read_text(encoding="utf-8"))
    assert "requiresE0" in catalog
    assert catalog["course"]["id"]
    assert catalog["course"]["title"]
```

- [ ] **Step 8: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest tests/test_fixtures.py -v`

Expected: `test_no_placeholder_hashes_remain` FAILS listing three files; the hash tests FAIL too.

- [ ] **Step 9: Compute and substitute the real hashes**

Run this one-off helper from the repository root, then paste each printed value over its `REPLACED_IN_STEP_7` placeholder:

```bash
cd agent-native/e0/tests/fixtures/course
python3 - <<'PY'
import hashlib, json, pathlib
root = pathlib.Path(".")
for path in root.rglob("questions.json"):
    bank = json.loads(path.read_text())
    for q in bank["questions"]:
        if q["type"] == "mcq":
            print(path, q["id"], hashlib.sha256(q["options"][0].encode()).hexdigest())
for path in root.rglob("checks/checks.json"):
    for name in json.loads(path.read_text())["files"]:
        print(path, name, hashlib.sha256((path.parent / name).read_bytes()).hexdigest())
PY
```

The correct option is the first one in every fixture bank. Substitute each hash into the
matching `answerHash` and `files` entry.

- [ ] **Step 10: Run the tests to verify they pass**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: all tests pass, including the 6 from Task 1.

- [ ] **Step 11: Commit**

```bash
git add agent-native/
git commit -m "test(e0): fixture course with validated hashes and repo fixtures"
```

---

### Task 3: State Layer — Repo Discovery, Events, and Profile

**Files:**
- Modify: `agent-native/e0/bin/e0`
- Create: `agent-native/e0/tests/test_state.py`

**Interfaces:**
- Consumes: `ok`, `problem`, `COMMANDS` from Task 1; `student_repo` fixture from Task 2
- Produces:
  - `run_git(cwd, *args) -> tuple[int, str, str]` — never raises
  - `repo_root(start=None) -> pathlib.Path | None`
  - `exit0_dir(root) -> pathlib.Path`
  - `require_repo(command) -> tuple[Path | None, dict | None]` — the second element is a
    ready-to-return problem payload. `require_content` in Task 5 follows the identical
    convention, so every command handler starts with the same two-line guard.
  - `append_event(root, event: str, **fields) -> dict`
  - `read_events(root) -> list[dict]` — skips malformed lines
  - `detect_profile(root) -> dict` with keys `os`, `shell`, `testFramework`
  - `read_profile(root) -> dict`, `write_profile(root, profile) -> None`
  - `cmd_profile(args)` registered as `profile`

- [ ] **Step 1: Write the failing tests**

Create `agent-native/e0/tests/test_state.py`:

```python
import json


def test_repo_root_finds_the_git_root_from_a_subdirectory(e0mod, student_repo):
    nested = student_repo / "src" / "deep"
    nested.mkdir(parents=True)
    assert e0mod.repo_root(nested) == student_repo


def test_repo_root_returns_none_outside_a_repo(e0mod, tmp_path):
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    assert e0mod.repo_root(outside) is None


def test_run_git_never_raises_on_a_bad_command(e0mod, student_repo):
    code, out, err = e0mod.run_git(student_repo, "definitely-not-a-git-command")
    assert code != 0
    assert isinstance(out, str) and isinstance(err, str)


def test_append_and_read_events_roundtrip(e0mod, student_repo):
    e0mod.append_event(student_repo, "task_started", taskId="T010")
    e0mod.append_event(student_repo, "task_completed", taskId="T010")
    events = e0mod.read_events(student_repo)

    assert [event["event"] for event in events] == ["task_started", "task_completed"]
    assert events[0]["taskId"] == "T010"
    assert "ts" in events[0]


def test_read_events_skips_malformed_lines(e0mod, student_repo):
    e0mod.append_event(student_repo, "task_started", taskId="T010")
    log = e0mod.exit0_dir(student_repo) / "state" / "events.jsonl"
    with log.open("a", encoding="utf-8") as handle:
        handle.write("this is not json\n")
    e0mod.append_event(student_repo, "task_completed", taskId="T010")

    events = e0mod.read_events(student_repo)
    assert [event["event"] for event in events] == ["task_started", "task_completed"]


def test_read_events_on_a_fresh_repo_is_empty(e0mod, student_repo):
    assert e0mod.read_events(student_repo) == []


def test_detect_profile_reports_a_known_os(e0mod, student_repo):
    profile = e0mod.detect_profile(student_repo)
    assert profile["os"] in {"linux", "macos", "windows"}
    assert "shell" in profile
    assert profile["testFramework"] in {"pytest", "unittest"}


def test_detect_profile_finds_pytest_from_requirements(e0mod, student_repo):
    (student_repo / "requirements.txt").write_text("pytest==8.0.0\n", encoding="utf-8")
    assert e0mod.detect_profile(student_repo)["testFramework"] == "pytest"


def test_profile_get_and_set_via_the_command(run_e0, student_repo):
    payload, code = run_e0(["profile", "set", "testFramework", "unittest"], student_repo)
    assert code == 0 and payload["ok"] is True

    payload, _ = run_e0(["profile", "get"], student_repo)
    assert payload["data"]["profile"]["testFramework"] == "unittest"


def test_profile_set_without_a_value_is_a_problem(run_e0, student_repo):
    payload, code = run_e0(["profile", "set", "testFramework"], student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "value" in payload["guidance"].lower()


def test_commands_outside_a_git_repo_give_guidance(run_e0, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    payload, code = run_e0(["profile", "get"], outside)
    assert code == 0
    assert payload["ok"] is False
    assert "git" in payload["guidance"].lower()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest tests/test_state.py -v`

Expected: FAIL with `AttributeError: module 'e0' has no attribute 'repo_root'`.

- [ ] **Step 3: Implement the state layer**

In `agent-native/e0/bin/e0`, replace the `import json` / `import sys` block at the top with:

```python
import datetime
import json
import os
import pathlib
import platform
import subprocess
import sys
```

Then insert this section immediately after the envelope helpers and before the commands section:

```python
# ---------------------------------------------------------------- process


def run_git(cwd, *args):
    """Run a git command. Returns (returncode, stdout, stderr) and never raises."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except OSError as exc:
        return 127, "", str(exc)


# ---------------------------------------------------------------- paths


def repo_root(start=None):
    """The git top level containing `start`, or None if there is not one."""
    base = pathlib.Path(start) if start is not None else pathlib.Path.cwd()
    code, out, _ = run_git(base, "rev-parse", "--show-toplevel")
    if code != 0 or not out:
        return None
    return pathlib.Path(out)


def exit0_dir(root):
    return pathlib.Path(root) / ".exit0"


def state_dir(root):
    return exit0_dir(root) / "state"


def require_repo(command):
    """Return (root, None) or (None, problem_payload)."""
    root = repo_root()
    if root is None:
        return None, problem(
            command,
            "e0 could not find a git repository here.",
            "Run e0 from inside your forked course repository. "
            "If you have not cloned it yet, clone your fork first.",
        )
    return root, None


# ---------------------------------------------------------------- state


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def append_event(root, event, **fields):
    record = {"ts": _now(), "event": event}
    record.update(fields)
    directory = state_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    return record


def read_events(root):
    path = state_dir(root) / "events.jsonl"
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            continue  # a corrupted line must never stop the course
    return events


def _detect_os():
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    return "linux"


def _detect_shell():
    shell = os.environ.get("SHELL") or os.environ.get("COMSPEC") or ""
    return pathlib.Path(shell).name or "unknown"


def _detect_test_framework(root):
    candidates = ["requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.cfg"]
    for name in candidates:
        path = pathlib.Path(root) / name
        if path.exists() and "pytest" in path.read_text(encoding="utf-8", errors="replace"):
            return "pytest"
    return "unittest"


def detect_profile(root):
    return {
        "os": _detect_os(),
        "shell": _detect_shell(),
        "testFramework": _detect_test_framework(root),
    }


def read_profile(root):
    path = state_dir(root) / "profile.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def write_profile(root, profile):
    directory = state_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "profile.json").write_text(
        json.dumps(profile, indent=2) + "\n", encoding="utf-8"
    )
```

- [ ] **Step 4: Add the `profile` command**

In the commands section of `agent-native/e0/bin/e0`, add before `cmd_help`:

```python
def cmd_profile(args):
    root, failure = require_repo("profile")
    if failure:
        return failure

    action = args[0] if args else "get"
    profile = read_profile(root) or detect_profile(root)

    if action == "get":
        return ok(
            "profile",
            {"profile": profile},
            "Detected: " + ", ".join(f"{k}={v}" for k, v in sorted(profile.items())),
        )

    if action == "set":
        if len(args) < 3:
            return problem(
                "profile",
                "e0 profile set needs a key and a value.",
                "Use: e0 profile set <key> <value>",
            )
        key, value = args[1], args[2]
        profile[key] = value
        write_profile(root, profile)
        append_event(root, "profile_set", key=key, value=value)
        return ok("profile", {"profile": profile}, f"Recorded {key}={value}.")

    return problem(
        "profile",
        f"Unknown profile action '{action}'.",
        "Use 'e0 profile get' or 'e0 profile set <key> <value>'.",
    )
```

Register it in the dispatch table:

```python
COMMANDS = {
    "help": cmd_help,
    "profile": cmd_profile,
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add agent-native/
git commit -m "feat(e0): repo discovery, event log, and profile detection"
```

---

### Task 4: `e0 init`

**Files:**
- Modify: `agent-native/e0/bin/e0`
- Create: `agent-native/e0/tests/test_init.py`

**Interfaces:**
- Consumes: everything from Task 3; `content_repo`, `student_repo`, `framework_dir`, `make_course_repo` fixtures from Task 2
- Produces:
  - `read_exit0_json(root) -> dict` — the template repo's course declaration
  - `course_repo_url(root) -> str | None` — `E0_CONTENT_REPO` overrides `exit0.json`
  - `framework_path(root) -> pathlib.Path` — `E0_FRAMEWORK_DIR` overrides `.exit0/framework`
  - `e0_supports(requirement: str) -> bool`
  - `latest_tag(url) -> str | None`
  - `fetch_course(root, url, tag) -> pathlib.Path`
  - `install_skills(root) -> list[str]` — framework skills, then course skills layered over
  - `ensure_gitignored(root) -> bool` — returns True if it added the entry
  - `read_catalog(root) -> dict | None`
  - `cmd_init(args)` registered as `init`

- [ ] **Step 1: Write the failing tests**

Create `agent-native/e0/tests/test_init.py`:

```python
import json


def test_latest_tag_reads_the_newest_tag(e0mod, content_repo):
    assert e0mod.latest_tag(str(content_repo)) == "v0.1.0"


def test_latest_tag_on_an_unreachable_url_returns_none(e0mod, tmp_path):
    assert e0mod.latest_tag(str(tmp_path / "nope")) is None


def test_init_creates_the_exit0_tree(run_e0, student_repo, content_repo):
    payload, code = run_e0(
        ["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)}
    )

    assert code == 0
    assert payload["ok"] is True

    exit0 = student_repo / ".exit0"
    assert (exit0 / "course" / "catalog.json").exists()
    assert (exit0 / "state" / "profile.json").exists()
    assert (exit0 / "README.md").exists()


def test_init_finds_its_course_from_exit0_json(run_e0, student_repo, content_repo):
    """The framework is course-agnostic; the template repo names its course."""
    (student_repo / "exit0.json").write_text(
        json.dumps({"courseRepo": str(content_repo)}), encoding="utf-8"
    )
    payload, code = run_e0(["init"], student_repo)

    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["course"]["id"] == "demo"


def test_init_without_any_course_declaration_gives_guidance(run_e0, tmp_path):
    import subprocess

    bare = tmp_path / "bare"
    bare.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(bare), check=True)

    payload, code = run_e0(["init"], bare)
    assert code == 0
    assert payload["ok"] is False
    assert "exit0.json" in payload["guidance"]


def test_e0_supports_compares_versions(e0mod):
    assert e0mod.e0_supports("1.0") is True
    assert e0mod.e0_supports("0.9") is True
    assert e0mod.e0_supports("99.0") is False
    assert e0mod.e0_supports("") is True
    assert e0mod.e0_supports("nonsense") is True


def test_init_refuses_a_course_that_needs_a_newer_framework(
    run_e0, student_repo, make_course_repo
):
    def bump(catalog):
        catalog["requiresE0"] = "99.0"

    repo = make_course_repo(mutate_catalog=bump)
    payload, code = run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(repo)})

    assert code == 0
    assert payload["ok"] is False
    assert "99.0" in payload["problem"]
    assert "update" in payload["guidance"].lower()


def test_init_installs_framework_skills(
    run_e0, student_repo, content_repo, framework_dir
):
    payload, _ = run_e0(
        ["init"],
        student_repo,
        env={
            "E0_CONTENT_REPO": str(content_repo),
            "E0_FRAMEWORK_DIR": str(framework_dir),
        },
    )
    assert payload["ok"] is True
    assert (student_repo / ".exit0" / "skills").is_dir()


def test_init_succeeds_even_when_the_framework_dir_is_missing(
    run_e0, student_repo, content_repo, tmp_path
):
    payload, code = run_e0(
        ["init"],
        student_repo,
        env={
            "E0_CONTENT_REPO": str(content_repo),
            "E0_FRAMEWORK_DIR": str(tmp_path / "no-framework-here"),
        },
    )
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["skills"] == []


def test_init_reports_the_pinned_tag_and_course_title(run_e0, student_repo, content_repo):
    payload, _ = run_e0(
        ["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)}
    )
    assert payload["data"]["contentTag"] == "v0.1.0"
    assert payload["data"]["course"]["title"] == "Demo Course"


def test_init_adds_exit0_to_gitignore_without_touching_other_lines(
    run_e0, student_repo, content_repo
):
    gitignore = student_repo / ".gitignore"
    gitignore.write_text("*.pyc\n.venv/\n", encoding="utf-8")

    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})

    lines = gitignore.read_text(encoding="utf-8").splitlines()
    assert "*.pyc" in lines
    assert ".venv/" in lines
    assert ".exit0/" in lines


def test_init_does_not_duplicate_the_gitignore_entry(run_e0, student_repo, content_repo):
    env = {"E0_CONTENT_REPO": str(content_repo)}
    run_e0(["init"], student_repo, env=env)
    run_e0(["init"], student_repo, env=env)

    lines = (student_repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert lines.count(".exit0/") == 1


def test_init_is_idempotent(run_e0, student_repo, content_repo):
    env = {"E0_CONTENT_REPO": str(content_repo)}
    first, _ = run_e0(["init"], student_repo, env=env)
    second, code = run_e0(["init"], student_repo, env=env)

    assert code == 0
    assert second["ok"] is True
    assert first["data"]["contentTag"] == second["data"]["contentTag"]


def test_init_records_an_event(run_e0, student_repo, content_repo, e0mod):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    events = e0mod.read_events(student_repo)
    assert any(event["event"] == "initialized" for event in events)


def test_init_with_an_unreachable_course_repo_is_a_problem_not_a_crash(
    run_e0, student_repo, tmp_path
):
    payload, code = run_e0(
        ["init"], student_repo, env={"E0_CONTENT_REPO": str(tmp_path / "missing")}
    )
    assert code == 0
    assert payload["ok"] is False
    assert payload["guidance"]


def test_init_writes_a_warning_readme(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    readme = (student_repo / ".exit0" / "README.md").read_text(encoding="utf-8")
    assert "do not edit" in readme.lower()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest tests/test_init.py -v`

Expected: FAIL with `AttributeError: module 'e0' has no attribute 'latest_tag'`.

- [ ] **Step 3: Implement content fetch**

Add to `agent-native/e0/bin/e0`, after the state section:

```python
# ---------------------------------------------------------------- course

DEFAULT_FRAMEWORK_DIR = ".exit0/framework"

EXIT0_README = """# .exit0/

This directory is managed by `e0`, the Exit Zero framework CLI. **Do not edit it by hand**
and do not commit it — it is gitignored on purpose.

Everything here can be deleted and rebuilt. Run `e0 init` to restore it.

- `framework/` the Exit Zero framework itself
- `course/`    the course you are taking, pinned to a released version
- `skills/`    how your agent runs the course
- `tasks/`     your tasks, personalized for your machine
- `state/`     what you have done so far
- `bin/`       the `e0` CLI

Some files here are lightly obfuscated — answer keys are stored as hashes, and some
instructor notes are base64. That is a speed bump, not a lock. If you go looking you
will find them. We would rather you did not: the questions only help you if you answer
them honestly.
"""


def read_exit0_json(root):
    """The template repo's declaration of which course this is."""
    path = pathlib.Path(root) / "exit0.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def course_repo_url(root):
    override = os.environ.get("E0_CONTENT_REPO")
    if override:
        return override
    return read_exit0_json(root).get("courseRepo") or None


def framework_path(root):
    override = os.environ.get("E0_FRAMEWORK_DIR")
    if override:
        return pathlib.Path(override)
    return pathlib.Path(root) / DEFAULT_FRAMEWORK_DIR


def _version_tuple(value):
    parts = []
    for chunk in str(value).split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        if digits == "":
            return None
        parts.append(int(digits))
    return tuple(parts) if parts else None


def e0_supports(requirement):
    """True unless the course demands a newer framework than this one.

    Unparseable or absent requirements are treated as satisfied — refusing to run over a
    malformed version string would be a dead end for no benefit.
    """
    wanted = _version_tuple(requirement) if requirement else None
    if wanted is None:
        return True
    mine = _version_tuple(E0_VERSION) or (0,)
    return mine >= wanted


def latest_tag(url):
    code, out, _ = run_git(
        pathlib.Path.cwd(),
        "ls-remote",
        "--tags",
        "--refs",
        "--sort=-v:refname",
        url,
    )
    if code != 0 or not out:
        return None
    first = out.splitlines()[0]
    if "refs/tags/" not in first:
        return None
    return first.split("refs/tags/", 1)[1].strip()


def fetch_course(root, url, tag):
    """Clone the course content repo at `tag` into .exit0/course, replacing what is there."""
    import shutil

    destination = exit0_dir(root) / "course"
    staging = exit0_dir(root) / ".course-staging"

    if staging.exists():
        shutil.rmtree(staging)
    staging.parent.mkdir(parents=True, exist_ok=True)

    code, _, err = run_git(
        staging.parent, "clone", "--quiet", "--depth", "1", "--branch", tag, url, str(staging)
    )
    if code != 0:
        if staging.exists():
            shutil.rmtree(staging)
        raise RuntimeError(err or f"could not clone {url} at {tag}")

    shutil.rmtree(staging / ".git", ignore_errors=True)
    if destination.exists():
        shutil.rmtree(destination)
    staging.rename(destination)
    return destination


def install_skills(root):
    """Framework skills first, then any course skills layered over them."""
    import shutil

    destination = exit0_dir(root) / "skills"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    installed = []
    for source in (
        framework_path(root) / "skills",
        exit0_dir(root) / "course" / "skills",
    ):
        if not source.is_dir():
            continue
        for item in sorted(source.glob("*.md")):
            shutil.copy2(item, destination / item.name)
            if item.stem not in installed:
                installed.append(item.stem)
    return installed


def ensure_gitignored(root):
    path = pathlib.Path(root) / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if any(line.strip() == ".exit0/" for line in existing.splitlines()):
        return False
    prefix = "" if existing == "" or existing.endswith("\n") else "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{prefix}.exit0/\n")
    return True


def read_catalog(root):
    path = exit0_dir(root) / "course" / "catalog.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
```

- [ ] **Step 4: Add the `init` command**

Add to the commands section:

```python
def cmd_init(args):
    root, failure = require_repo("init")
    if failure:
        return failure

    url = course_repo_url(root)
    if not url:
        return problem(
            "init",
            "e0 does not know which course this repository belongs to.",
            "A course template repo declares this in exit0.json at its root, like "
            '{"courseRepo": "https://github.com/exit0/polybot-content.git"}. '
            "If you forked a course template, that file should already be there.",
        )

    tag = latest_tag(url)
    if tag is None:
        return problem(
            "init",
            f"e0 could not reach the course content at {url}.",
            "Check your network connection and try again. "
            "If you are offline, everything already downloaded still works.",
        )

    try:
        fetch_course(root, url, tag)
    except Exception as exc:  # noqa: BLE001
        return problem(
            "init",
            f"e0 could not download the course: {exc}",
            "Check your network connection and try 'e0 init' again.",
        )

    catalog = read_catalog(root)
    if catalog is None:
        return problem(
            "init",
            "The downloaded course has no readable catalog.json.",
            "This is a problem with the course, not with you. Please report it.",
        )

    required = catalog.get("requiresE0", "")
    if not e0_supports(required):
        return problem(
            "init",
            f"This course needs Exit Zero {required}, and you have {E0_VERSION}.",
            "Update the framework: delete .exit0/framework and let your agent "
            "re-run the bootstrap step from AGENTS.md.",
        )

    profile = read_profile(root) or detect_profile(root)
    write_profile(root, profile)
    skills = install_skills(root)

    exit0_dir(root).mkdir(parents=True, exist_ok=True)
    (exit0_dir(root) / "README.md").write_text(EXIT0_README, encoding="utf-8")
    (exit0_dir(root) / "tasks").mkdir(exist_ok=True)
    added_ignore = ensure_gitignored(root)

    course = catalog.get("course", {})
    append_event(root, "initialized", contentTag=tag, course=course.get("id"))

    return ok(
        "init",
        {
            "contentTag": tag,
            "course": course,
            "profile": profile,
            "skills": skills,
            "taskCount": len(catalog.get("tasks", [])),
            "addedGitignoreEntry": added_ignore,
        },
        f"Ready. {course.get('title', 'The course')} is set up at {tag} "
        f"with {len(catalog.get('tasks', []))} tasks.",
    )
```

Register it:

```python
COMMANDS = {
    "help": cmd_help,
    "init": cmd_init,
    "profile": cmd_profile,
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add agent-native/
git commit -m "feat(e0): init - resolve the course, fetch it pinned, install framework skills"
```

---

### Task 5: `e0 catalog`

**Files:**
- Modify: `agent-native/e0/bin/e0`
- Create: `agent-native/e0/tests/test_catalog.py`

**Interfaces:**
- Consumes: `read_catalog`, `read_events` from Tasks 3–4
- Produces:
  - `task_status(root) -> dict[str, str]` — task id → one of `not_started`, `in_progress`, `complete`
  - `find_task(catalog, task_id) -> dict | None` — case-insensitive on the id
  - `cmd_catalog(args)` registered as `catalog`

- [ ] **Step 1: Write the failing tests**

Create `agent-native/e0/tests/test_catalog.py`:

```python
import pytest


@pytest.fixture
def initialized(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    return student_repo


def test_catalog_lists_every_task_in_order(run_e0, initialized):
    payload, code = run_e0(["catalog"], initialized)
    assert code == 0
    assert [task["id"] for task in payload["data"]["tasks"]] == ["T010", "T020"]


def test_catalog_reports_dependencies_and_status(run_e0, initialized):
    payload, _ = run_e0(["catalog"], initialized)
    second = payload["data"]["tasks"][1]
    assert second["dependsOn"] == ["T010"]
    assert second["status"] == "not_started"


def test_status_reflects_recorded_events(run_e0, initialized, e0mod):
    e0mod.append_event(initialized, "task_started", taskId="T010")
    payload, _ = run_e0(["catalog"], initialized)
    statuses = {task["id"]: task["status"] for task in payload["data"]["tasks"]}
    assert statuses["T010"] == "in_progress"

    e0mod.append_event(initialized, "task_completed", taskId="T010")
    payload, _ = run_e0(["catalog"], initialized)
    statuses = {task["id"]: task["status"] for task in payload["data"]["tasks"]}
    assert statuses["T010"] == "complete"


def test_find_task_is_case_insensitive(e0mod, initialized):
    catalog = e0mod.read_catalog(initialized)
    assert e0mod.find_task(catalog, "t010")["id"] == "T010"
    assert e0mod.find_task(catalog, "T010")["id"] == "T010"
    assert e0mod.find_task(catalog, "T999") is None


def test_catalog_before_init_gives_guidance(run_e0, student_repo):
    payload, code = run_e0(["catalog"], student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "init" in payload["guidance"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest tests/test_catalog.py -v`

Expected: FAIL — `catalog` is an unknown command, so `payload["data"]["tasks"]` raises `KeyError`.

- [ ] **Step 3: Implement status derivation and the command**

Add to the course section of `agent-native/e0/bin/e0`:

```python
def find_task(catalog, task_id):
    if not catalog:
        return None
    wanted = str(task_id).strip().lower()
    for task in catalog.get("tasks", []):
        if task["id"].lower() == wanted:
            return task
    return None


def task_status(root):
    """Derive each task's status from the event log. Later events win."""
    statuses = {}
    for event in read_events(root):
        task_id = event.get("taskId")
        if not task_id:
            continue
        if event["event"] == "task_started":
            statuses[task_id] = "in_progress"
        elif event["event"] == "task_completed":
            statuses[task_id] = "complete"
    return statuses


def require_content(command, root):
    """Return (catalog, None) or (None, problem_payload)."""
    catalog = read_catalog(root)
    if catalog is None:
        return None, problem(
            command,
            "The course content is not downloaded yet.",
            "Run 'e0 init' to download it.",
        )
    return catalog, None
```

Add the command:

```python
def cmd_catalog(args):
    root, failure = require_repo("catalog")
    if failure:
        return failure

    catalog, failure = require_content("catalog", root)
    if failure:
        return failure

    statuses = task_status(root)
    tasks = []
    for task in sorted(catalog.get("tasks", []), key=lambda item: item.get("order", 0)):
        tasks.append(
            {
                "id": task["id"],
                "title": task["title"],
                "description": task.get("description", ""),
                "labels": task.get("labels", []),
                "dependsOn": task.get("dependsOn", []),
                "relatedTopics": task.get("relatedTopics", []),
                "status": statuses.get(task["id"], "not_started"),
            }
        )

    done = sum(1 for task in tasks if task["status"] == "complete")
    return ok(
        "catalog",
        {"tasks": tasks, "contentTag": catalog.get("contentTag")},
        f"{len(tasks)} tasks, {done} complete.",
    )
```

Register it in `COMMANDS` as `"catalog": cmd_catalog,`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add agent-native/
git commit -m "feat(e0): catalog with status derived from the event log"
```

---

### Task 6: `e0 status`

**Files:**
- Modify: `agent-native/e0/bin/e0`
- Create: `agent-native/e0/tests/test_status.py`

**Interfaces:**
- Consumes: `task_status`, `find_task`, `latest_tag` from Tasks 4–5
- Produces:
  - `next_task(catalog, statuses) -> dict | None` — lowest `order` not complete
  - `unmet_dependencies(task, statuses) -> list[str]`
  - `cmd_status(args)` registered as `status`, and set as `DEFAULT_COMMAND`

- [ ] **Step 1: Write the failing tests**

Create `agent-native/e0/tests/test_status.py`:

```python
import pytest


@pytest.fixture
def initialized(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    return student_repo


def test_status_on_a_fresh_course_suggests_the_first_task(run_e0, initialized):
    payload, code = run_e0(["status"], initialized)
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["next"]["id"] == "T010"
    assert payload["data"]["current"] is None


def test_status_reports_the_task_in_progress(run_e0, initialized, e0mod):
    e0mod.append_event(initialized, "task_started", taskId="T010")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["current"]["id"] == "T010"


def test_next_task_skips_completed_work(e0mod, initialized):
    catalog = e0mod.read_catalog(initialized)
    statuses = {"T010": "complete"}
    assert e0mod.next_task(catalog, statuses)["id"] == "T020"


def test_next_task_is_none_when_everything_is_done(e0mod, initialized):
    catalog = e0mod.read_catalog(initialized)
    statuses = {"T010": "complete", "T020": "complete"}
    assert e0mod.next_task(catalog, statuses) is None


def test_unmet_dependencies_lists_incomplete_prerequisites(e0mod, initialized):
    catalog = e0mod.read_catalog(initialized)
    task = e0mod.find_task(catalog, "T020")
    assert e0mod.unmet_dependencies(task, {}) == ["T010"]
    assert e0mod.unmet_dependencies(task, {"T010": "complete"}) == []


def test_status_reports_update_availability_as_a_string(run_e0, initialized, content_repo):
    payload, _ = run_e0(
        ["status"], initialized, env={"E0_CONTENT_REPO": str(content_repo)}
    )
    assert payload["data"]["update"] in {"current", "available", "unknown"}


def test_status_says_unknown_when_the_course_repo_is_unreachable(
    run_e0, initialized, tmp_path
):
    payload, code = run_e0(
        ["status"], initialized, env={"E0_CONTENT_REPO": str(tmp_path / "gone")}
    )
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["update"] == "unknown"


def test_bare_e0_runs_status(run_e0, initialized):
    payload, code = run_e0([], initialized)
    assert code == 0
    assert payload["command"] == "status"


def test_status_before_init_gives_guidance(run_e0, student_repo):
    payload, code = run_e0(["status"], student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "init" in payload["guidance"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest tests/test_status.py -v`

Expected: FAIL — `status` is not a registered command.

- [ ] **Step 3: Implement**

Add to the content section:

```python
def next_task(catalog, statuses):
    ordered = sorted(catalog.get("tasks", []), key=lambda item: item.get("order", 0))
    for task in ordered:
        if statuses.get(task["id"]) != "complete":
            return task
    return None


def unmet_dependencies(task, statuses):
    return [
        dependency
        for dependency in task.get("dependsOn", [])
        if statuses.get(dependency) != "complete"
    ]
```

Add the command:

```python
def cmd_status(args):
    root, failure = require_repo("status")
    if failure:
        return failure

    catalog, failure = require_content("status", root)
    if failure:
        return failure

    statuses = task_status(root)
    current = None
    for task in catalog.get("tasks", []):
        if statuses.get(task["id"]) == "in_progress":
            current = {"id": task["id"], "title": task["title"]}
            break

    upcoming = next_task(catalog, statuses)
    upcoming_summary = None
    if upcoming is not None:
        upcoming_summary = {
            "id": upcoming["id"],
            "title": upcoming["title"],
            "unmetDependencies": unmet_dependencies(upcoming, statuses),
        }

    pinned = catalog.get("contentTag")
    available = latest_tag(course_repo_url(root) or "")
    if available is None:
        update = "unknown"
    elif available != pinned:
        update = "available"
    else:
        update = "current"

    completed = [task_id for task_id, state in statuses.items() if state == "complete"]

    if current:
        message = f"You are working on {current['id']}: {current['title']}."
    elif upcoming_summary:
        message = f"Nothing in progress. Next up is {upcoming_summary['id']}: {upcoming_summary['title']}."
    else:
        message = "Every task is complete."

    return ok(
        "status",
        {
            "current": current,
            "next": upcoming_summary,
            "completed": sorted(completed),
            "contentTag": pinned,
            "latestTag": available,
            "update": update,
        },
        message,
    )
```

Register it and make it the default:

```python
COMMANDS = {
    "catalog": cmd_catalog,
    "help": cmd_help,
    "init": cmd_init,
    "profile": cmd_profile,
    "status": cmd_status,
}

DEFAULT_COMMAND = "status"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add agent-native/
git commit -m "feat(e0): status with next-task selection and update check"
```

---

### Task 7: Region Marker Parser

The heart of the personalization contract. A pure function with no filesystem or process access, tested exhaustively.

**Files:**
- Modify: `agent-native/e0/bin/e0`
- Create: `agent-native/e0/tests/test_markers.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `parse_regions(text: str) -> list[dict]` — ordered segments, each `{"kind": "fixed"|"variant"|"retone", "text": str, ...}`. Variant segments carry `id` and `branches` (a list of `{"when": dict, "text": str}`). Retone segments carry `basedOn` and `text`.
  - `parse_when(value: str) -> dict` — `"os=macos shell=zsh"` → `{"os": "macos", "shell": "zsh"}`
  - `select_branch(branches: list, facts: dict) -> dict | None`
  - `MarkerError` — raised only by `parse_regions` on malformed input, always caught by callers

- [ ] **Step 1: Write the failing tests**

Create `agent-native/e0/tests/test_markers.py`:

```python
import pytest

PLAIN = """# Title

Some prose.
"""

WITH_VARIANT = """Intro.

<!-- e0:variant id="install" -->
<!-- when: os=macos -->
```bash
brew install ffmpeg
```
<!-- when: os=linux -->
```bash
sudo apt install ffmpeg
```
<!-- /e0:variant -->

Outro.
"""

WITH_RETONE = """Intro.

<!-- e0:retone based-on="the student's Linux knowledge" -->
<!-- /e0:retone -->

Outro.
"""


def test_plain_text_is_one_fixed_segment(e0mod):
    regions = e0mod.parse_regions(PLAIN)
    assert len(regions) == 1
    assert regions[0]["kind"] == "fixed"
    assert regions[0]["text"] == PLAIN


def test_variant_is_isolated_between_fixed_segments(e0mod):
    regions = e0mod.parse_regions(WITH_VARIANT)
    kinds = [region["kind"] for region in regions]
    assert kinds == ["fixed", "variant", "fixed"]
    assert regions[0]["text"].startswith("Intro.")
    assert regions[2]["text"].strip() == "Outro."


def test_variant_branches_are_parsed_with_conditions(e0mod):
    variant = e0mod.parse_regions(WITH_VARIANT)[1]
    assert variant["id"] == "install"
    assert len(variant["branches"]) == 2
    assert variant["branches"][0]["when"] == {"os": "macos"}
    assert "brew install ffmpeg" in variant["branches"][0]["text"]
    assert variant["branches"][1]["when"] == {"os": "linux"}
    assert "sudo apt install ffmpeg" in variant["branches"][1]["text"]


def test_branch_text_preserves_fenced_code_blocks(e0mod):
    variant = e0mod.parse_regions(WITH_VARIANT)[1]
    assert variant["branches"][0]["text"].count("```") == 2


def test_retone_block_records_its_basis_and_body(e0mod):
    regions = e0mod.parse_regions(WITH_RETONE)
    retone = regions[1]
    assert retone["kind"] == "retone"
    assert retone["basedOn"] == "the student's Linux knowledge"
    assert retone["text"].strip() == ""


def test_parse_when_handles_multiple_conditions(e0mod):
    assert e0mod.parse_when("os=macos shell=zsh") == {"os": "macos", "shell": "zsh"}
    assert e0mod.parse_when("os=linux") == {"os": "linux"}
    assert e0mod.parse_when("") == {}


def test_select_branch_matches_on_facts(e0mod):
    branches = [
        {"when": {"os": "macos"}, "text": "brew"},
        {"when": {"os": "linux"}, "text": "apt"},
    ]
    assert e0mod.select_branch(branches, {"os": "linux"})["text"] == "apt"
    assert e0mod.select_branch(branches, {"os": "windows"}) is None


def test_select_branch_requires_every_condition_to_match(e0mod):
    branches = [{"when": {"os": "linux", "shell": "fish"}, "text": "fishy"}]
    assert e0mod.select_branch(branches, {"os": "linux"}) is None
    assert e0mod.select_branch(branches, {"os": "linux", "shell": "fish"}) is not None


def test_unclosed_variant_raises_marker_error(e0mod):
    with pytest.raises(e0mod.MarkerError):
        e0mod.parse_regions('<!-- e0:variant id="x" -->\nno closing tag\n')


def test_closing_without_opening_raises_marker_error(e0mod):
    with pytest.raises(e0mod.MarkerError):
        e0mod.parse_regions("text\n<!-- /e0:variant -->\n")


def test_nested_regions_raise_marker_error(e0mod):
    with pytest.raises(e0mod.MarkerError):
        e0mod.parse_regions(
            '<!-- e0:variant id="a" -->\n<!-- e0:variant id="b" -->\n'
            "<!-- /e0:variant -->\n<!-- /e0:variant -->\n"
        )


def test_roundtrip_reassembles_the_original_text(e0mod):
    for source in (PLAIN, WITH_VARIANT, WITH_RETONE):
        regions = e0mod.parse_regions(source)
        rebuilt = "".join(region["raw"] for region in regions)
        assert rebuilt == source
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest tests/test_markers.py -v`

Expected: FAIL with `AttributeError: module 'e0' has no attribute 'parse_regions'`.

- [ ] **Step 3: Implement the parser**

Add `import re` to the imports. Add this section after the content section:

```python
# ---------------------------------------------------------------- markers

OPEN_VARIANT = re.compile(r'^\s*<!--\s*e0:variant\s+id="([^"]+)"\s*-->\s*$')
CLOSE_VARIANT = re.compile(r"^\s*<!--\s*/e0:variant\s*-->\s*$")
OPEN_RETONE = re.compile(r'^\s*<!--\s*e0:retone(?:\s+based-on="([^"]*)")?\s*-->\s*$')
CLOSE_RETONE = re.compile(r"^\s*<!--\s*/e0:retone\s*-->\s*$")
WHEN = re.compile(r"^\s*<!--\s*when:\s*(.*?)\s*-->\s*$")


class MarkerError(Exception):
    """Raised when region markers are malformed. Callers always catch this."""


def parse_when(value):
    conditions = {}
    for token in (value or "").split():
        if "=" not in token:
            continue
        key, _, val = token.partition("=")
        conditions[key.strip()] = val.strip()
    return conditions


def _split_branches(lines):
    """Turn the inside of a variant block into a list of branches."""
    branches = []
    current = None
    for line in lines:
        match = WHEN.match(line)
        if match:
            current = {"when": parse_when(match.group(1)), "lines": []}
            branches.append(current)
            continue
        if current is None:
            if line.strip():
                raise MarkerError(
                    "content inside a variant block before the first 'when:' marker"
                )
            continue
        current["lines"].append(line)
    return [
        {"when": branch["when"], "text": "".join(branch["lines"]).strip("\n")}
        for branch in branches
    ]


def parse_regions(text):
    """Split a document into ordered fixed / variant / retone segments.

    Every segment carries `raw`, so concatenating them reproduces the input exactly.
    """
    lines = text.splitlines(keepends=True)
    regions = []
    buffer = []
    index = 0

    def flush_fixed():
        if buffer:
            blob = "".join(buffer)
            regions.append({"kind": "fixed", "text": blob, "raw": blob})
            buffer.clear()

    while index < len(lines):
        line = lines[index]

        if CLOSE_VARIANT.match(line) or CLOSE_RETONE.match(line):
            raise MarkerError(f"closing marker without an opening one on line {index + 1}")

        open_variant = OPEN_VARIANT.match(line)
        open_retone = OPEN_RETONE.match(line)

        if not open_variant and not open_retone:
            buffer.append(line)
            index += 1
            continue

        flush_fixed()
        opener = line
        body = []
        closer_pattern = CLOSE_VARIANT if open_variant else CLOSE_RETONE
        other_opener = OPEN_RETONE if open_variant else OPEN_VARIANT
        index += 1

        while index < len(lines) and not closer_pattern.match(lines[index]):
            if OPEN_VARIANT.match(lines[index]) or other_opener.match(lines[index]):
                raise MarkerError(f"nested region marker on line {index + 1}")
            body.append(lines[index])
            index += 1

        if index >= len(lines):
            raise MarkerError("region opened but never closed")

        closer = lines[index]
        index += 1
        raw = opener + "".join(body) + closer

        if open_variant:
            regions.append(
                {
                    "kind": "variant",
                    "id": open_variant.group(1),
                    "branches": _split_branches(body),
                    "text": "".join(body),
                    "raw": raw,
                }
            )
        else:
            regions.append(
                {
                    "kind": "retone",
                    "basedOn": open_retone.group(1) or "",
                    "text": "".join(body),
                    "raw": raw,
                }
            )

    flush_fixed()
    return regions


def select_branch(branches, facts):
    for branch in branches:
        if all(facts.get(key) == value for key, value in branch["when"].items()):
            return branch
    return None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add agent-native/
git commit -m "feat(e0): region marker parser for the personalization contract"
```

---

### Task 8: `e0 start`

**Files:**
- Modify: `agent-native/e0/bin/e0`
- Create: `agent-native/e0/tests/test_start.py`

**Interfaces:**
- Consumes: `parse_regions`, `find_task`, `task_status`, `unmet_dependencies`, `read_profile`
- Produces:
  - `task_dir(root, task_id) -> pathlib.Path` — `.exit0/tasks/<lowercased id>/`
  - `sha256_file(path) -> str`
  - `copy_checks(root, task_id) -> dict` — returns `{"copied": [...], "mismatched": [...]}`
  - `personalization_payload(canonical_text, profile) -> dict`
  - `cmd_start(args)` registered as `start`

- [ ] **Step 1: Write the failing tests**

Create `agent-native/e0/tests/test_start.py`:

```python
import pytest


@pytest.fixture
def initialized(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    return student_repo


def test_start_writes_task_and_canonical_copies(run_e0, initialized):
    payload, code = run_e0(["start", "T010"], initialized)

    assert code == 0
    assert payload["ok"] is True

    task_dir = initialized / ".exit0" / "tasks" / "t010"
    assert (task_dir / "task.md").exists()
    assert (task_dir / "task.canonical.md").exists()
    assert (task_dir / "task.md").read_text(encoding="utf-8") == (
        task_dir / "task.canonical.md"
    ).read_text(encoding="utf-8")


def test_start_copies_the_check_files(run_e0, initialized):
    run_e0(["start", "T010"], initialized)
    checks = initialized / ".exit0" / "tasks" / "t010" / "checks"
    assert (checks / "test_greeting.py").exists()
    assert (checks / "checks.json").exists()


def test_start_accepts_a_lowercase_task_id(run_e0, initialized):
    payload, _ = run_e0(["start", "t010"], initialized)
    assert payload["ok"] is True
    assert payload["data"]["taskId"] == "T010"


def test_start_emits_the_issue_title_and_body(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    assert payload["data"]["issue"]["title"] == "[T010] Say hello"
    assert "Say hello" in payload["data"]["issue"]["body"]


def test_start_emits_variants_with_their_branches(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    variants = payload["data"]["personalization"]["variants"]
    assert len(variants) == 1
    assert variants[0]["id"] == "run-tests"
    assert {tuple(sorted(b["when"].items())) for b in variants[0]["branches"]} == {
        (("os", "linux"),),
        (("os", "macos"),),
        (("os", "windows"),),
    }


def test_start_emits_retone_blocks(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    blocks = payload["data"]["personalization"]["retoneBlocks"]
    assert len(blocks) == 1
    assert blocks[0]["basedOn"] == "the student's Python experience"


def test_start_emits_only_facts_referenced_by_variants(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    facts = payload["data"]["personalization"]["facts"]
    assert set(facts) == {"os"}


def test_start_includes_the_decoded_rules(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    assert "function" in payload["data"]["rules"]


def test_start_warns_about_unmet_dependencies_but_proceeds(run_e0, initialized):
    payload, code = run_e0(["start", "T020"], initialized)

    assert code == 0
    assert payload["ok"] is True
    warnings = payload["data"]["warnings"]
    assert any(warning["kind"] == "dependency" for warning in warnings)
    assert (initialized / ".exit0" / "tasks" / "t020" / "task.md").exists()


def test_start_records_an_override_event_for_unmet_dependencies(
    run_e0, initialized, e0mod
):
    run_e0(["start", "T020"], initialized)
    events = e0mod.read_events(initialized)
    assert any(event["event"] == "override" for event in events)


def test_start_records_a_task_started_event(run_e0, initialized, e0mod):
    run_e0(["start", "T010"], initialized)
    events = e0mod.read_events(initialized)
    started = [event for event in events if event["event"] == "task_started"]
    assert started and started[-1]["taskId"] == "T010"


def test_start_with_an_unknown_task_lists_valid_ids(run_e0, initialized):
    payload, code = run_e0(["start", "T999"], initialized)
    assert code == 0
    assert payload["ok"] is False
    assert "T010" in payload["guidance"]


def test_start_without_a_task_id_is_a_problem(run_e0, initialized):
    payload, code = run_e0(["start"], initialized)
    assert code == 0
    assert payload["ok"] is False


def test_start_does_not_overwrite_an_existing_personalized_task(run_e0, initialized):
    run_e0(["start", "T010"], initialized)
    task_file = initialized / ".exit0" / "tasks" / "t010" / "task.md"
    task_file.write_text("personalized already\n", encoding="utf-8")

    payload, _ = run_e0(["start", "T010"], initialized)

    assert task_file.read_text(encoding="utf-8") == "personalized already\n"
    assert payload["data"]["alreadyStarted"] is True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest tests/test_start.py -v`

Expected: FAIL — `start` is not a registered command.

- [ ] **Step 3: Implement the helpers**

Add `import base64` and `import hashlib` to the imports. Add after the markers section:

```python
# ---------------------------------------------------------------- tasks


def task_dir(root, task_id):
    return exit0_dir(root) / "tasks" / task_id.lower()


def content_task_dir(root, task_id):
    return exit0_dir(root) / "course" / "tasks" / task_id.lower()


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def read_task_rules(root, task_id):
    """Course-wide rules plus this task's rules, decoded if base64."""
    parts = []
    for candidate in (
        exit0_dir(root) / "course" / "rules.md",
        content_task_dir(root, task_id) / "rules.md",
    ):
        if not candidate.exists():
            continue
        raw = candidate.read_text(encoding="utf-8")
        parts.append(_maybe_decode(raw))
    return "\n\n".join(part.strip() for part in parts if part.strip())


def _maybe_decode(raw):
    """Decode base64-obfuscated rules; return the text unchanged if it is plain."""
    stripped = "".join(raw.split())
    if not stripped or not re.fullmatch(r"[A-Za-z0-9+/=]+", stripped):
        return raw
    try:
        return base64.b64decode(stripped, validate=True).decode("utf-8")
    except Exception:  # noqa: BLE001
        return raw


def copy_checks(root, task_id):
    """Copy check files into the working copy and verify their hashes."""
    import shutil

    source = content_task_dir(root, task_id) / "checks"
    destination = task_dir(root, task_id) / "checks"
    result = {"copied": [], "mismatched": []}
    if not source.exists():
        return result

    destination.mkdir(parents=True, exist_ok=True)
    spec_path = source / "checks.json"
    expected = {}
    if spec_path.exists():
        try:
            expected = json.loads(spec_path.read_text(encoding="utf-8")).get("files", {})
        except ValueError:
            expected = {}

    for item in sorted(source.iterdir()):
        if not item.is_file():
            continue
        shutil.copy2(item, destination / item.name)
        result["copied"].append(item.name)
        if item.name in expected and sha256_file(item) != expected[item.name]:
            result["mismatched"].append(item.name)

    return result


def personalization_payload(canonical_text, profile):
    """What the agent is permitted to act on — and nothing else."""
    regions = parse_regions(canonical_text)
    variants = []
    retone_blocks = []
    referenced_keys = set()

    for region in regions:
        if region["kind"] == "variant":
            variants.append({"id": region["id"], "branches": region["branches"]})
            for branch in region["branches"]:
                referenced_keys.update(branch["when"].keys())
        elif region["kind"] == "retone":
            retone_blocks.append({"basedOn": region["basedOn"]})

    facts = {key: profile[key] for key in sorted(referenced_keys) if key in profile}
    return {"variants": variants, "retoneBlocks": retone_blocks, "facts": facts}
```

- [ ] **Step 4: Implement the command**

```python
def cmd_start(args):
    root, failure = require_repo("start")
    if failure:
        return failure

    catalog, failure = require_content("start", root)
    if failure:
        return failure

    if not args:
        available = ", ".join(task["id"] for task in catalog.get("tasks", []))
        return problem(
            "start",
            "e0 start needs a task id.",
            f"Use: e0 start <id>. Available tasks: {available}",
        )

    task = find_task(catalog, args[0])
    if task is None:
        available = ", ".join(item["id"] for item in catalog.get("tasks", []))
        return problem(
            "start",
            f"There is no task called '{args[0]}'.",
            f"Available tasks: {available}",
        )

    task_id = task["id"]
    source = content_task_dir(root, task_id) / "task.md"
    if not source.exists():
        return problem(
            "start",
            f"Task {task_id} has no task.md in the course content.",
            "This is a problem with the course, not with you. Please report it.",
        )

    canonical_text = source.read_text(encoding="utf-8")
    working = task_dir(root, task_id)
    working.mkdir(parents=True, exist_ok=True)
    (working / "task.canonical.md").write_text(canonical_text, encoding="utf-8")

    already_started = (working / "task.md").exists()
    if not already_started:
        (working / "task.md").write_text(canonical_text, encoding="utf-8")

    checks = copy_checks(root, task_id)

    statuses = task_status(root)
    unmet = unmet_dependencies(task, statuses)
    warnings = []
    if unmet:
        warnings.append(
            {
                "kind": "dependency",
                "message": (
                    f"{task_id} builds on {', '.join(unmet)}, which "
                    f"{'is' if len(unmet) == 1 else 'are'} not complete yet. "
                    "You can carry on, but expect to be missing context."
                ),
            }
        )
        append_event(root, "override", taskId=task_id, unmet=unmet)

    for name in checks["mismatched"]:
        warnings.append(
            {
                "kind": "check_hash",
                "message": f"The check file {name} does not match its published hash.",
            }
        )

    profile = read_profile(root) or detect_profile(root)
    try:
        payload = personalization_payload(canonical_text, profile)
        marker_problem = None
    except MarkerError as exc:
        payload = {"variants": [], "retoneBlocks": [], "facts": {}}
        marker_problem = str(exc)
        warnings.append(
            {
                "kind": "markers",
                "message": f"The task's personalization markers are malformed ({exc}). "
                "The task text is still correct; it just will not be personalized.",
            }
        )

    append_event(root, "task_started", taskId=task_id)

    body = (
        f"{task.get('description', '')}\n\n"
        f"Working through **{task['title']}**.\n\n"
        f"Task text: `.exit0/tasks/{task_id.lower()}/task.md`"
    ).strip()

    return ok(
        "start",
        {
            "taskId": task_id,
            "title": task["title"],
            "alreadyStarted": already_started,
            "paths": {
                "task": f".exit0/tasks/{task_id.lower()}/task.md",
                "canonical": f".exit0/tasks/{task_id.lower()}/task.canonical.md",
                "checks": f".exit0/tasks/{task_id.lower()}/checks",
            },
            "relatedTopics": task.get("relatedTopics", []),
            "warnings": warnings,
            "personalization": payload,
            "markerProblem": marker_problem,
            "rules": read_task_rules(root, task_id),
            "issue": {"title": f"[{task_id}] {task['title']}", "body": body},
        },
        f"{task_id} is ready at .exit0/tasks/{task_id.lower()}/task.md.",
    )
```

Register `"start": cmd_start,` in `COMMANDS`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add agent-native/
git commit -m "feat(e0): start - materialize a task with checks and personalization payload"
```

---

### Task 9: `e0 verify`

**Files:**
- Modify: `agent-native/e0/bin/e0`
- Create: `agent-native/e0/tests/test_verify.py`

**Interfaces:**
- Consumes: `parse_regions`, `task_dir`
- Produces:
  - `verify_document(canonical_text, personalized_text) -> dict` with keys `violations` (list) and `restored` (str, the corrected document)
  - `cmd_verify(args)` registered as `verify`, accepting a path or a task id

- [ ] **Step 1: Write the failing tests**

Create `agent-native/e0/tests/test_verify.py`:

```python
import pytest

CANONICAL = """# Task

Build the agent using **langchain**.

<!-- e0:variant id="install" -->
<!-- when: os=macos -->
brew install ffmpeg
<!-- when: os=linux -->
sudo apt install ffmpeg
<!-- /e0:variant -->

<!-- e0:retone based-on="experience" -->
<!-- /e0:retone -->

Done.
"""


def _personalize(variant_body, retone_body, fixed_tail="Done.\n"):
    return (
        "# Task\n\nBuild the agent using **langchain**.\n\n"
        '<!-- e0:variant id="install" -->\n'
        f"{variant_body}"
        "<!-- /e0:variant -->\n\n"
        '<!-- e0:retone based-on="experience" -->\n'
        f"{retone_body}"
        "<!-- /e0:retone -->\n\n"
        f"{fixed_tail}"
    )


def test_unchanged_document_has_no_violations(e0mod):
    result = e0mod.verify_document(CANONICAL, CANONICAL)
    assert result["violations"] == []
    assert result["restored"] == CANONICAL


def test_selecting_a_declared_branch_is_allowed(e0mod):
    personalized = _personalize("sudo apt install ffmpeg\n", "")
    result = e0mod.verify_document(CANONICAL, personalized)
    assert result["violations"] == []


def test_inventing_a_branch_is_a_violation(e0mod):
    personalized = _personalize("nix-env -i ffmpeg\n", "")
    result = e0mod.verify_document(CANONICAL, personalized)
    assert len(result["violations"]) == 1
    assert result["violations"][0]["kind"] == "variant"
    assert result["violations"][0]["id"] == "install"


def test_filling_a_retone_block_is_allowed(e0mod):
    personalized = _personalize(
        "sudo apt install ffmpeg\n", "You have done this before, so skim it.\n"
    )
    result = e0mod.verify_document(CANONICAL, personalized)
    assert result["violations"] == []


def test_editing_fixed_prose_is_a_violation(e0mod):
    personalized = _personalize("sudo apt install ffmpeg\n", "").replace(
        "**langchain**", "**langgraph**"
    )
    result = e0mod.verify_document(CANONICAL, personalized)

    assert any(violation["kind"] == "fixed" for violation in result["violations"])
    assert "**langchain**" in result["restored"]
    assert "**langgraph**" not in result["restored"]


def test_restored_document_keeps_allowed_personalization(e0mod):
    personalized = _personalize(
        "sudo apt install ffmpeg\n", "Skim this.\n"
    ).replace("**langchain**", "**langgraph**")
    result = e0mod.verify_document(CANONICAL, personalized)

    assert "**langchain**" in result["restored"]
    assert "sudo apt install ffmpeg" in result["restored"]
    assert "Skim this." in result["restored"]


def test_deleting_a_region_is_a_violation(e0mod):
    personalized = "# Task\n\nBuild the agent using **langchain**.\n\nDone.\n"
    result = e0mod.verify_document(CANONICAL, personalized)
    assert any(violation["kind"] == "structure" for violation in result["violations"])
    assert result["restored"] == CANONICAL


def test_verify_command_restores_the_file_on_disk(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    run_e0(["start", "T010"], student_repo)

    task_file = student_repo / ".exit0" / "tasks" / "t010" / "task.md"
    tampered = task_file.read_text(encoding="utf-8").replace(
        "**standard library**", "**requests**"
    )
    task_file.write_text(tampered, encoding="utf-8")

    payload, code = run_e0(["verify", "T010"], student_repo)

    assert code == 0
    assert payload["ok"] is False
    assert payload["data"]["violations"]
    assert "**standard library**" in task_file.read_text(encoding="utf-8")


def test_verify_command_on_a_clean_document_passes(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    run_e0(["start", "T010"], student_repo)

    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert payload["ok"] is True


def test_verify_without_a_target_is_a_problem(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    payload, code = run_e0(["verify"], student_repo)
    assert code == 0
    assert payload["ok"] is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest tests/test_verify.py -v`

Expected: FAIL with `AttributeError: module 'e0' has no attribute 'verify_document'`.

- [ ] **Step 3: Implement verification**

Add to the markers section:

```python
def verify_document(canonical_text, personalized_text):
    """Check a personalized document against its canonical form.

    Returns {"violations": [...], "restored": str}. The restored document keeps every
    legal personalization and reverts everything else.
    """
    canonical = parse_regions(canonical_text)

    try:
        personalized = parse_regions(personalized_text)
    except MarkerError as exc:
        return {
            "violations": [
                {
                    "kind": "structure",
                    "message": f"The document's region markers are malformed: {exc}",
                }
            ],
            "restored": canonical_text,
        }

    shapes_match = len(canonical) == len(personalized) and all(
        left["kind"] == right["kind"] for left, right in zip(canonical, personalized)
    )
    if not shapes_match:
        return {
            "violations": [
                {
                    "kind": "structure",
                    "message": "Regions were added, removed, or reordered. "
                    "The document has been restored to its original form.",
                }
            ],
            "restored": canonical_text,
        }

    violations = []
    rebuilt = []

    for original, edited in zip(canonical, personalized):
        if original["kind"] == "fixed":
            if original["raw"] != edited["raw"]:
                violations.append(
                    {
                        "kind": "fixed",
                        "message": "Text outside an editable region was changed. "
                        "It has been restored.",
                    }
                )
                rebuilt.append(original["raw"])
            else:
                rebuilt.append(edited["raw"])

        elif original["kind"] == "variant":
            chosen = edited["text"].strip()
            allowed = [branch["text"].strip() for branch in original["branches"]]
            if chosen in allowed or chosen == original["text"].strip():
                rebuilt.append(edited["raw"])
            else:
                violations.append(
                    {
                        "kind": "variant",
                        "id": original["id"],
                        "message": f"Variant '{original['id']}' does not match any "
                        "declared branch. It has been restored.",
                    }
                )
                rebuilt.append(original["raw"])

        else:  # retone — free text by design
            rebuilt.append(edited["raw"])

    return {"violations": violations, "restored": "".join(rebuilt)}
```

- [ ] **Step 4: Implement the command**

```python
def cmd_verify(args):
    root, failure = require_repo("verify")
    if failure:
        return failure

    if not args:
        return problem(
            "verify",
            "e0 verify needs a task id or a file path.",
            "Use: e0 verify <taskId>  or  e0 verify <path/to/task.md>",
        )

    target = args[0]
    candidate = task_dir(root, target) / "task.md"
    if candidate.exists():
        personalized_path = candidate
        canonical_path = task_dir(root, target) / "task.canonical.md"
    else:
        personalized_path = pathlib.Path(root) / target
        canonical_path = personalized_path.with_name(
            personalized_path.stem + ".canonical" + personalized_path.suffix
        )

    if not personalized_path.exists() or not canonical_path.exists():
        return problem(
            "verify",
            f"e0 could not find both the document and its canonical copy for '{target}'.",
            "Run 'e0 start <taskId>' first, which writes both files.",
        )

    try:
        result = verify_document(
            canonical_path.read_text(encoding="utf-8"),
            personalized_path.read_text(encoding="utf-8"),
        )
    except MarkerError as exc:
        return problem(
            "verify",
            f"The canonical document has malformed markers: {exc}",
            "This is a problem with the course, not with you. Please report it.",
        )

    if not result["violations"]:
        return ok(
            "verify",
            {"violations": [], "path": str(personalized_path.relative_to(root))},
            "Personalization is within the contract.",
        )

    personalized_path.write_text(result["restored"], encoding="utf-8")
    append_event(
        root,
        "verify_restored",
        path=str(personalized_path.relative_to(root)),
        count=len(result["violations"]),
    )

    payload = problem(
        "verify",
        "The personalized document changed content it is not allowed to change. "
        + " ".join(violation["message"] for violation in result["violations"]),
        "e0 has restored the protected text. Re-apply personalization only inside "
        "e0:variant and e0:retone regions.",
    )
    payload["data"] = {"violations": result["violations"]}
    return payload
```

- [ ] **Step 5: Register and run the tests**

Add `"verify": cmd_verify,` to `COMMANDS`.

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add agent-native/
git commit -m "feat(e0): verify - mechanical enforcement of the personalization contract"
```

---

### Task 10: `e0 check`

**Files:**
- Modify: `agent-native/e0/bin/e0`
- Create: `agent-native/e0/tests/test_check.py`

**Interfaces:**
- Consumes: `task_dir`, `sha256_file`, `task_status`
- Produces:
  - `check_hashes(root, task_id) -> list[str]` — names of drifted files
  - `cmd_check(args)` registered as `check`

- [ ] **Step 1: Write the failing tests**

Create `agent-native/e0/tests/test_check.py`:

```python
import pytest


@pytest.fixture
def started(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    run_e0(["start", "T010"], student_repo)
    return student_repo


def test_check_fails_before_the_student_writes_any_code(run_e0, started):
    payload, code = run_e0(["check", "T010"], started)
    assert code == 0
    assert payload["ok"] is False
    assert payload["data"]["passed"] is False


def test_check_passes_once_the_code_is_correct(run_e0, started):
    (started / "greeting.py").write_text(
        'def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8"
    )
    payload, code = run_e0(["check", "T010"], started)

    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["passed"] is True


def test_check_reports_test_output(run_e0, started):
    (started / "greeting.py").write_text(
        'def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8"
    )
    payload, _ = run_e0(["check", "T010"], started)
    assert "test_greet_returns_expected_string" in payload["data"]["output"]


def test_check_warns_when_a_test_file_has_drifted(run_e0, started):
    check_file = started / ".exit0" / "tasks" / "t010" / "checks" / "test_greeting.py"
    check_file.write_text("# oops I edited this\n", encoding="utf-8")

    payload, _ = run_e0(["check", "T010"], started)
    assert any(warning["kind"] == "check_hash" for warning in payload["data"]["warnings"])


def test_check_hashes_detects_drift(e0mod, started):
    assert e0mod.check_hashes(started, "T010") == []

    check_file = started / ".exit0" / "tasks" / "t010" / "checks" / "test_greeting.py"
    check_file.write_text("# edited\n", encoding="utf-8")
    assert e0mod.check_hashes(started, "T010") == ["test_greeting.py"]


def test_check_uses_the_in_progress_task_by_default(run_e0, started):
    payload, _ = run_e0(["check"], started)
    assert payload["data"]["taskId"] == "T010"


def test_check_on_a_task_that_was_never_started_gives_guidance(run_e0, started):
    payload, code = run_e0(["check", "T020"], started)
    assert code == 0
    assert payload["ok"] is False
    assert "start" in payload["guidance"]


def test_check_records_an_event(run_e0, started, e0mod):
    run_e0(["check", "T010"], started)
    events = e0mod.read_events(started)
    assert any(event["event"] == "checks_run" for event in events)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest tests/test_check.py -v`

Expected: FAIL — `check` is not registered.

- [ ] **Step 3: Implement**

Add to the tasks section:

```python
def read_checks_spec(root, task_id):
    path = task_dir(root, task_id) / "checks" / "checks.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


def check_hashes(root, task_id):
    """Names of check files whose contents no longer match checks.json."""
    spec = read_checks_spec(root, task_id)
    if not spec:
        return []
    checks = task_dir(root, task_id) / "checks"
    drifted = []
    for name, expected in spec.get("files", {}).items():
        candidate = checks / name
        if not candidate.exists() or sha256_file(candidate) != expected:
            drifted.append(name)
    return sorted(drifted)


def run_checks(root, task_id):
    """Run the task's checks. Returns (passed, combined_output)."""
    spec = read_checks_spec(root, task_id)
    if not spec or not spec.get("run"):
        return False, "This task has no runnable checks."

    checks = task_dir(root, task_id) / "checks"
    command = [
        part.replace("{checks_dir}", str(checks)) for part in spec["run"]
    ]
    try:
        proc = subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return False, "The checks took longer than 5 minutes and were stopped."
    except OSError as exc:
        return False, f"e0 could not run the checks: {exc}"

    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()
```

Add the command:

```python
def cmd_check(args):
    root, failure = require_repo("check")
    if failure:
        return failure

    catalog, failure = require_content("check", root)
    if failure:
        return failure

    if args:
        task = find_task(catalog, args[0])
        if task is None:
            return problem(
                "check",
                f"There is no task called '{args[0]}'.",
                "Run 'e0 catalog' to see the task ids.",
            )
        task_id = task["id"]
    else:
        statuses = task_status(root)
        in_progress = [
            item["id"]
            for item in catalog.get("tasks", [])
            if statuses.get(item["id"]) == "in_progress"
        ]
        if not in_progress:
            return problem(
                "check",
                "No task is in progress, so e0 does not know what to check.",
                "Use 'e0 check <taskId>', or 'e0 start <taskId>' to begin one.",
            )
        task_id = in_progress[0]

    if not (task_dir(root, task_id) / "checks").exists():
        return problem(
            "check",
            f"The checks for {task_id} are not on disk yet.",
            f"Run 'e0 start {task_id}' first.",
        )

    warnings = [
        {
            "kind": "check_hash",
            "message": f"{name} no longer matches the published version. "
            "Your local result may be misleading — CI always uses the original.",
        }
        for name in check_hashes(root, task_id)
    ]

    passed, output = run_checks(root, task_id)
    append_event(root, "checks_run", taskId=task_id, passed=passed)

    data = {
        "taskId": task_id,
        "passed": passed,
        "output": output,
        "warnings": warnings,
    }

    if passed:
        return ok("check", data, f"All checks for {task_id} pass.")

    payload = problem(
        "check",
        f"The checks for {task_id} are not passing yet.",
        "Read the failure output, change your code, and run 'e0 check' again.",
    )
    payload["data"] = data
    return payload
```

Register `"check": cmd_check,`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add agent-native/
git commit -m "feat(e0): check - run school checks with drift detection"
```

---

### Task 11: Course Template Repo and Bootstrap

**Files:**
- Create: `agent-native/courses/demo/template/README.md`
- Create: `agent-native/courses/demo/template/AGENTS.md`
- Create: `agent-native/courses/demo/template/CLAUDE.md`
- Create: `agent-native/courses/demo/template/exit0.json`
- Create: `agent-native/courses/demo/template/.github/copilot-instructions.md`
- Create: `agent-native/courses/demo/template/.gitignore`
- Create: `agent-native/e0/tests/test_template.py`

**Interfaces:**
- Consumes: the `e0` command surface from Tasks 4–10
- Produces: the fork target for one course, and the bootstrap chain that works before `.exit0/`
  exists

- [ ] **Step 1: Write the failing tests**

Create `agent-native/e0/tests/test_template.py`:

```python
import json
import pathlib
import re

TEMPLATE = (
    pathlib.Path(__file__).resolve().parents[2] / "courses" / "demo" / "template"
)
E0_PATH = pathlib.Path(__file__).resolve().parents[1] / "bin" / "e0"


def test_template_has_the_required_files():
    for name in (
        "README.md",
        "AGENTS.md",
        "CLAUDE.md",
        "exit0.json",
        ".github/copilot-instructions.md",
        ".gitignore",
    ):
        assert (TEMPLATE / name).exists(), f"missing {name}"


def test_exit0_json_names_the_course_content_repo():
    """The framework is course-agnostic; the template must say what it belongs to."""
    declaration = json.loads((TEMPLATE / "exit0.json").read_text(encoding="utf-8"))
    assert declaration["courseRepo"].startswith("http")
    assert declaration["courseRepo"].endswith(".git")


def test_readme_tells_the_student_to_say_hi():
    readme = (TEMPLATE / "README.md").read_text(encoding="utf-8").lower()
    assert "fork" in readme
    assert "hi" in readme


def test_readme_does_not_ask_the_student_to_install_anything():
    readme = (TEMPLATE / "README.md").read_text(encoding="utf-8").lower()
    for forbidden in ("pip install", "npm install", "brew install", "apt install"):
        assert forbidden not in readme


def test_agents_md_bootstraps_the_framework_before_using_it():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    bootstrap_at = agents.find(".exit0/framework")
    status_at = agents.find("e0 status")
    assert bootstrap_at != -1, "AGENTS.md must describe fetching the framework"
    assert status_at != -1
    assert bootstrap_at < status_at, "bootstrap must come before any e0 usage"


def test_pointer_files_redirect_to_agents_md():
    for name in ("CLAUDE.md", ".github/copilot-instructions.md"):
        text = (TEMPLATE / name).read_text(encoding="utf-8")
        assert "AGENTS.md" in text
        assert len(text.splitlines()) <= 6, f"{name} should be a pointer, not a copy"


def test_gitignore_excludes_exit0():
    lines = (TEMPLATE / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".exit0/" in lines


def test_every_e0_command_agents_md_mentions_actually_exists():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    source = E0_PATH.read_text(encoding="utf-8")
    registered = set(re.findall(r'^\s{4}"([a-z-]+)": cmd_', source, re.MULTILINE))
    mentioned = set(re.findall(r"`e0 ([a-z-]+)", agents))
    assert mentioned <= registered, f"AGENTS.md mentions unknown commands: {mentioned - registered}"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest tests/test_template.py -v`

Expected: FAIL — the template directory does not exist.

- [ ] **Step 3: Create the README**

Create `agent-native/courses/demo/template/README.md`:

```markdown
# Demo Course

A hands-on course you work through with your coding agent, on the Exit Zero framework.

## Getting started

1. Fork this repository, then clone your fork.
2. Open it in VS Code, or your editor of choice.
3. Open the chat panel and say **hi**.

That's it. Your agent takes it from here — it will set everything up, explain how the
course works, and get you started on the first task.

## A note on cost

This course is designed to run on a **cheap model** — Haiku, GPT-mini, or similar. All the
teaching content, tests, and rules are written by humans and handed to your agent; it does
not need to reason its way through them. Switch to your agent's cheapest model before you
start. You will get the same experience for a fraction of the cost.
```

- [ ] **Step 4: Declare the course**

Create `agent-native/courses/demo/template/exit0.json`:

```json
{
  "courseRepo": "https://github.com/exit0/demo-content.git"
}
```

This is the only file that ties a fork to a course. `e0` reads it and knows nothing else
about which course it is running.

- [ ] **Step 5: Create `AGENTS.md`**

Create `agent-native/courses/demo/template/AGENTS.md`:

````markdown
# Working with this repository

This is a course running on **Exit Zero**, an agent-native learning framework. The student
learns by doing tasks in this repository, and you are their guide. The framework's CLI,
`e0`, holds all the course logic — which task is next, what the rules are, whether their
work passes. **Ask `e0`; do not guess.**

## Before anything else: install the framework

Exit Zero is not committed to this repository. On your first turn in a fresh clone, check
for `.exit0/framework/`. If it is missing, fetch it:

```bash
git clone --depth 1 https://github.com/exit0/e0.git .exit0/framework
```

Then run `.exit0/framework/bin/e0 init`. That reads `exit0.json` to find out which course
this is, downloads it, and installs everything else — including the skills below.

After this point `.exit0/skills/` exists. **Read it.** Those files describe how to run a
course; this file only gets you to them.

## Every session

- Run `e0 status` at the start of a session, and again after anything task-related.
- Read the relevant file in `.exit0/skills/` before acting.
- Never edit anything in `.exit0/` by hand. It is generated and gitignored.

## The one rule about content

Course text is personalized only inside marked regions. Never change wording outside them —
not to improve it, not to modernize a library choice, not to shorten it. Every instruction
is deliberate. Run `e0 verify <taskId>` after personalizing; it will tell you if you
overstepped.

## Suggest a cheap model

If the student is on an expensive model, mention once that this course is built to run well
on the cheapest model available, and that switching saves them money without costing them
anything.
````

- [ ] **Step 6: Create the pointer files**

Create `agent-native/courses/demo/template/CLAUDE.md`:

```markdown
See [AGENTS.md](AGENTS.md) for how to work in this repository.
```

Create `agent-native/courses/demo/template/.github/copilot-instructions.md`:

```markdown
See [AGENTS.md](../AGENTS.md) for how to work in this repository.
```

Create `agent-native/courses/demo/template/.gitignore`:

```gitignore
.exit0/
__pycache__/
*.pyc
.venv/
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add agent-native/
git commit -m "feat(courses): demo course template with framework bootstrap"
```

---

### Task 12: Framework Skills

**Files:**
- Create: `agent-native/e0/skills/getting-started.md`
- Create: `agent-native/e0/skills/working-on-a-task.md`
- Create: `agent-native/e0/skills/using-the-knowledge-base.md`
- Create: `agent-native/e0/tests/fixtures/course/skills/demo-course-notes.md`
- Create: `agent-native/e0/tests/test_skills.py`
- Modify: `agent-native/e0/bin/e0` — register a `read` stub

**Interfaces:**
- Consumes: the `e0` command surface; `install_skills` from Task 4
- Produces: the framework's procedural layer, synced to `.exit0/skills/` by `e0 init`;
  `cmd_read` registered as `read` (a stub in this plan, implemented in plan 3)

- [ ] **Step 1: Write the failing tests**

Create `agent-native/e0/tests/test_skills.py`:

```python
import pathlib
import re

SKILLS = pathlib.Path(__file__).resolve().parents[1] / "skills"
E0_PATH = pathlib.Path(__file__).resolve().parents[1] / "bin" / "e0"

EXPECTED = {"getting-started", "working-on-a-task", "using-the-knowledge-base"}

# Courses hosted by the framework. None of these may appear in framework code or skills.
COURSE_NAMES = ("polybot", "yoloservice", "mit2026", "polyaidev", "demo course")


def test_every_expected_skill_exists():
    present = {path.stem for path in SKILLS.glob("*.md")}
    assert EXPECTED <= present


def test_skills_only_reference_real_commands():
    source = E0_PATH.read_text(encoding="utf-8")
    registered = set(re.findall(r'^\s{4}"([a-z-]+)": cmd_', source, re.MULTILINE))
    for path in SKILLS.glob("*.md"):
        mentioned = set(re.findall(r"`e0 ([a-z-]+)", path.read_text(encoding="utf-8")))
        assert mentioned <= registered, f"{path.name} references unknown: {mentioned - registered}"


def test_the_framework_names_no_course():
    """Exit Zero hosts courses. It must not know any of them by name."""
    targets = [E0_PATH, *SKILLS.glob("*.md")]
    for path in targets:
        text = path.read_text(encoding="utf-8").lower()
        for name in COURSE_NAMES:
            assert name not in text, f"{path.name} names the course '{name}'"


def test_working_on_a_task_requires_verify_after_personalizing():
    text = (SKILLS / "working-on-a-task.md").read_text(encoding="utf-8")
    assert "e0 verify" in text
    assert text.index("e0 start") < text.index("e0 verify")


def test_getting_started_mentions_the_cheap_model():
    text = (SKILLS / "getting-started.md").read_text(encoding="utf-8").lower()
    assert "cheap" in text or "cheapest" in text


def test_init_installs_framework_skills_and_layers_course_skills(
    run_e0, student_repo, content_repo, framework_dir
):
    run_e0(
        ["init"],
        student_repo,
        env={
            "E0_CONTENT_REPO": str(content_repo),
            "E0_FRAMEWORK_DIR": str(framework_dir),
        },
    )
    delivered = {
        path.stem for path in (student_repo / ".exit0" / "skills").glob("*.md")
    }
    assert EXPECTED <= delivered, "framework skills must be installed"
    assert "demo-course-notes" in delivered, "course skills must layer on top"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd agent-native/e0 && python -m pytest tests/test_skills.py -v`

Expected: FAIL — the skills directory does not exist.

- [ ] **Step 3: Write `getting-started.md`**

Create `agent-native/e0/skills/getting-started.md`:

```markdown
# Getting started

Use when the student first speaks to you in a course repository, or returns after a break.

## Steps

1. Run `e0 status`.
2. If it reports that the course is not set up, run `e0 init` and tell the student what
   happened in one sentence.
3. Suggest switching to their agent's cheapest model — once, briefly. This course hands you
   the content, tests, and rules; you are not reasoning from scratch, so an expensive model
   buys them nothing. Do not raise it again in the same session.
4. Tell them where they are:
   - Nothing started: name the first task and ask if they want to begin.
   - A task in progress: name it and ask if they want to continue.
   - Everything complete: say so.
5. If `status` reports `update: available`, mention it and offer to update. Do not update
   without being asked.

## Tone

Brief. The student wants to start, not to read a welcome tour. Two or three sentences.

## Never

- Never explain the whole course structure unprompted.
- Never start a task without being asked.
```

- [ ] **Step 4: Write `working-on-a-task.md`**

Create `agent-native/e0/skills/working-on-a-task.md`:

````markdown
# Working on a task

Use when the student wants to begin or continue a task.

## Starting

1. Run `e0 start <taskId>`.
2. If `warnings` contains a `dependency` entry, relay it honestly and let them choose:
   *"T020 builds on T010, which isn't done. Want to do that first, or push ahead?"*
   If they push ahead, help them — it is already recorded.
3. Personalize `task.md` using **only** what `personalization` gives you:
   - For each entry in `variants`, pick the one branch whose `when` conditions match
     `facts`. Delete the others and their `when:` markers. Never write a branch that is
     not listed.
   - Leave every `retone` block empty unless the student has explicitly asked for a note
     there. You have no basis for deciding what they already know.
   - Change nothing else. Not a word.
4. Run `e0 verify <taskId>`. If it reports violations, it has already restored the text —
   read what it says and do not repeat the mistake.
5. Open a GitHub issue using the `issue.title` and `issue.body` from `e0 start`, via `gh`
   or the GitHub MCP server, under the student's own account.
6. Point them at `.exit0/tasks/<id>/task.md` and let them read.

## While they work

The tests are already on disk, in `.exit0/tasks/<id>/checks/`. This is deliberate: read the
failing test first, then write the code that satisfies it.

Run `e0 check` when they want to know where they stand. If it reports a `check_hash`
warning, tell them their local copy of a test has drifted from the published one, so the
result may be misleading — CI always uses the original.

## Never

- Never edit files under `.exit0/` by hand; `e0` owns them.
- Never substitute a different library, tool, or approach for the one the task names. If
  the task says langchain, it means langchain, and there is a teaching reason.
- Never write the student's implementation for them. Explain, point at the failing test,
  ask what they think it wants.
````

- [ ] **Step 5: Write `using-the-knowledge-base.md`**

Create `agent-native/e0/skills/using-the-knowledge-base.md`:

```markdown
# Using the knowledge base

Use when the student asks about a concept, or asks to read a tutorial.

## What the knowledge base is

The course's own explanations of the concepts its tasks rely on. Every task lists its
related topics. `.exit0/course/knowledgebase/index.json` holds the title, topics, and a
one-line summary of each — read it, it is small and always on disk.

## When they ask about a covered topic

Say the course covers it, and point them at the tutorial. The course's explanation is the
one later tasks assume, so improvising a different one sets them up for confusion.

You may still answer their immediate question. Point at the tutorial as well, not instead.

## When they ask to read something

Run `e0 read <topic>`. It lands personalized on disk. Tell them the path.

## Never

- Never assess what the student knows. Do not quiz them to find out, and do not infer it
  from how they are doing. If they want a tutorial they will ask.
- Never tell them to go read something instead of answering. Answer, then point.
```

- [ ] **Step 6: Add a course-specific skill to the fixture**

Course skills are optional and layer over the framework's. The fixture course carries one so
the overlay path is exercised.

Create `agent-native/e0/tests/fixtures/course/skills/demo-course-notes.md`:

```markdown
# Demo course notes

Use alongside the framework skills, not instead of them.

This course is a two-task demonstration. Nothing in it is graded, and the checks are
deliberately small so the whole loop can be walked through in a few minutes.
```

- [ ] **Step 7: Register a `read` stub**

The `using-the-knowledge-base` skill written in Step 5 tells the agent to run `e0 read`, and
`test_skills_only_reference_real_commands` enforces that every command a skill names actually
exists. The full implementation belongs to plan 3, so register an honest stub now — one that
explains itself rather than looking broken.

Add to the commands section of `agent-native/e0/bin/e0`:

```python
def cmd_read(args):
    root, failure = require_repo("read")
    if failure:
        return failure

    topic = args[0] if args else ""
    index = exit0_dir(root) / "course" / "knowledgebase" / "index.json"
    location = f".exit0/course/knowledgebase/{topic}/tutorial.md" if topic else None

    return problem(
        "read",
        "Personalized tutorial delivery is not built yet.",
        (
            f"The tutorial is readable right now at {location}. "
            if location
            else ""
        )
        + f"Available topics are listed in {index.relative_to(root) if index.exists() else 'the course content'}.",
    )
```

Register `"read": cmd_read,` in `COMMANDS`.

- [ ] **Step 8: Run the tests to verify they pass**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
git add agent-native/
git commit -m "feat(e0): framework skills, course skill overlay, and read stub"
```

---

### Task 13: End-to-End Walkthrough

The test that proves the walking skeleton actually walks.

**Files:**
- Create: `agent-native/e0/tests/test_end_to_end.py`
- Modify: `agent-native/README.md`

**Interfaces:**
- Consumes: every command built so far
- Produces: a regression test covering the whole student journey

- [ ] **Step 1: Write the end-to-end test**

Create `agent-native/e0/tests/test_end_to_end.py`:

```python
import json
import subprocess


def test_a_student_can_go_from_fork_to_passing_checks(
    run_e0, student_repo, content_repo, e0mod
):
    env = {"E0_CONTENT_REPO": str(content_repo)}

    # 1. The agent bootstraps the course.
    payload, code = run_e0(["init"], student_repo, env=env)
    assert code == 0 and payload["ok"] is True
    assert payload["data"]["taskCount"] == 2

    # 2. The agent orients itself.
    payload, _ = run_e0(["status"], student_repo, env=env)
    assert payload["data"]["next"]["id"] == "T010"
    assert payload["data"]["current"] is None

    # 3. The student asks what the course covers.
    payload, _ = run_e0(["catalog"], student_repo, env=env)
    assert [task["id"] for task in payload["data"]["tasks"]] == ["T010", "T020"]

    # 4. The agent starts the first task.
    payload, _ = run_e0(["start", "T010"], student_repo, env=env)
    assert payload["data"]["warnings"] == []
    facts = payload["data"]["personalization"]["facts"]
    variant = payload["data"]["personalization"]["variants"][0]

    # 5. The agent personalizes: pick the matching branch, drop the rest.
    task_file = student_repo / ".exit0" / "tasks" / "t010" / "task.md"
    chosen = e0mod.select_branch(variant["branches"], facts)
    assert chosen is not None
    original = task_file.read_text(encoding="utf-8")
    start = original.index('<!-- e0:variant id="run-tests" -->')
    end = original.index("<!-- /e0:variant -->") + len("<!-- /e0:variant -->\n")
    personalized = (
        original[:start]
        + '<!-- e0:variant id="run-tests" -->\n'
        + chosen["text"]
        + "\n<!-- /e0:variant -->\n"
        + original[end:]
    )
    task_file.write_text(personalized, encoding="utf-8")

    # 6. Verification accepts a legal personalization.
    payload, code = run_e0(["verify", "T010"], student_repo, env=env)
    assert code == 0 and payload["ok"] is True

    # 7. Checks fail before any code is written.
    payload, _ = run_e0(["check", "T010"], student_repo, env=env)
    assert payload["data"]["passed"] is False

    # 8. The student writes the code.
    (student_repo / "greeting.py").write_text(
        'def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8"
    )

    # 9. Checks pass.
    payload, code = run_e0(["check", "T010"], student_repo, env=env)
    assert code == 0 and payload["ok"] is True
    assert payload["data"]["passed"] is True

    # 10. Nothing leaked into the student's git status.
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(student_repo),
        capture_output=True,
        text=True,
    )
    tracked_changes = [
        line for line in proc.stdout.splitlines() if ".exit0" in line
    ]
    assert tracked_changes == [], ".exit0/ must never appear in git status"


def test_pedagogical_drift_is_caught_and_reverted(run_e0, student_repo, content_repo):
    env = {"E0_CONTENT_REPO": str(content_repo)}
    run_e0(["init"], student_repo, env=env)
    run_e0(["start", "T010"], student_repo, env=env)

    task_file = student_repo / ".exit0" / "tasks" / "t010" / "task.md"
    task_file.write_text(
        task_file.read_text(encoding="utf-8").replace(
            "**standard library**", "**the requests library, which is nicer**"
        ),
        encoding="utf-8",
    )

    payload, code = run_e0(["verify", "T010"], student_repo, env=env)

    assert code == 0
    assert payload["ok"] is False
    restored = task_file.read_text(encoding="utf-8")
    assert "**standard library**" in restored
    assert "requests" not in restored


def test_every_command_survives_a_hostile_environment(run_e0, tmp_path, e0mod):
    """No command may crash, whatever state it is run in."""
    empty = tmp_path / "empty"
    empty.mkdir()

    invocations = [
        ["init"],
        ["status"],
        ["catalog"],
        ["start"],
        ["start", "NOPE"],
        ["verify"],
        ["verify", "NOPE"],
        ["check"],
        ["check", "NOPE"],
        ["profile", "get"],
        ["profile", "set"],
        ["profile", "nonsense"],
        ["help"],
        [],
        ["--version"],
        [""],
    ]

    for args in invocations:
        payload, code = run_e0(args, empty)
        assert code == 0, f"{args} exited {code}"
        assert isinstance(payload.get("ok"), bool), f"{args} produced no envelope"
        if payload["ok"] is False:
            assert payload["guidance"], f"{args} gave no guidance"
```

- [ ] **Step 2: Run the tests to verify they fail or reveal gaps**

Run: `cd agent-native/e0 && python -m pytest tests/test_end_to_end.py -v`

Expected: these should largely pass if Tasks 1–12 are correct. Any failure here is a real
integration bug — fix the implementation, not the test.

- [ ] **Step 3: Run the whole suite**

Run: `cd agent-native/e0 && python -m pytest -v`

Expected: every test passes.

- [ ] **Step 4: Update the directory README with the current command surface**

Append to `agent-native/README.md`:

```markdown
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
```

- [ ] **Step 5: Commit**

```bash
git add agent-native/
git commit -m "test(e0): end-to-end walkthrough and hostile-environment coverage"
```

---

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
