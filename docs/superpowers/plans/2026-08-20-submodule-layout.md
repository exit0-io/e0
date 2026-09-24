# Submodule Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the clone-at-init approach with two git submodules under `.exit0/` — one for the framework (`e0/`) and one for course content (`content/`) — eliminating `exit0.json`, `E0_CONTENT_REPO`, `E0_FRAMEWORK_DIR`, and all network calls from `e0 init`.

**Architecture:** The student's fork has `.exit0/e0/` (framework submodule: `bin/e0`, `skills/`) and `.exit0/content/` (course content submodule: `catalog.json`, `tasks/`, `knowledgebase/`). `git clone --recurse-submodules` delivers everything. `e0 init` only detects OS and writes a profile. Tests wire up real git submodules in fixtures instead of using env-var overrides.

**Tech Stack:** Python 3 stdlib, pytest, pytest-cov, git submodules.

## Global Constraints

- `e0` remains a single-file Python 3 script, stdlib only, no install step, never crashes (always exits 0, always prints valid JSON).
- Plain respectful language in all user-facing strings (short sentences, common words, no idioms).
- No `E0_CONTENT_REPO` or `E0_FRAMEWORK_DIR` env vars remain anywhere in the codebase after this plan is complete.
- State path: `.exit0/e0/state/` (inside the framework submodule working dir, gitignored by the framework repo's own `.gitignore`).
- Content path: `.exit0/content/` (the course content submodule working dir).
- Personalized task copies: `.exit0/tasks/` (gitignored by the student repo).

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `cli/bin/e0` | Modify | Remove dead code; update path constants; simplify `cmd_init`; update `cmd_status` |
| `cli/tests/conftest.py` | Rewrite | Submodule-based fixtures; remove env-var overrides |
| `cli/tests/test_init.py` | Rewrite | Remove obsolete tests; add submodule-not-initialized test |
| `cli/tests/test_status.py` | Modify | Drop env vars; drop update-check tests |
| `cli/tests/test_catalog.py` | Modify | Drop env vars from `initialized` fixture |
| `cli/tests/test_start.py` | Modify | Drop env vars from `initialized` fixture |
| `cli/tests/test_check.py` | Modify | Drop env vars from `started` fixture |
| `cli/tests/test_verify.py` | Modify | Drop env vars from setup |
| `cli/tests/test_skills.py` | Modify | Remove `test_init_installs_framework_skills_and_layers_course_skills` |
| `cli/tests/test_end_to_end.py` | Modify | Drop env vars |
| `cli/pytest.ini` | Modify | Add `--cov` flags |
| `courses/demo/template-repo/exit0.json` | Delete | Replaced by `.gitmodules` in real template repos |

---

## Task 1: Update `cli/bin/e0` — paths, dead code, simplified init

**Files:**
- Modify: `cli/bin/e0`

**Interfaces:**
- Removes: `read_exit0_json`, `course_repo_url`, `framework_path`, `latest_tag`, `fetch_course`, `install_skills`, `DEFAULT_FRAMEWORK_DIR`, `EXIT0_README`, `e0_supports`
- Adds: `content_dir(root)` → `Path`
- Changes: `state_dir(root)` now returns `exit0_dir(root) / "e0" / "state"`
- Changes: `content_task_dir(root, task_id)` now uses `content_dir`
- Changes: `cmd_init` signature unchanged, body replaced
- Changes: `cmd_status` no longer calls `latest_tag`; always emits `"update": "unknown"`

- [ ] **Step 1: Replace `state_dir` and add `content_dir`**

In `cli/bin/e0`, find the `state_dir` function and the block of path helpers. Replace:

```python
DEFAULT_FRAMEWORK_DIR = ".exit0/framework"
```
with nothing (delete the constant), and replace:

```python
def state_dir(root):
    return exit0_dir(root) / "state"
```
with:
```python
def content_dir(root):
    return exit0_dir(root) / "content"


def state_dir(root):
    return exit0_dir(root) / "e0" / "state"
```

- [ ] **Step 2: Update `content_task_dir` and `read_catalog`**

Replace:
```python
def read_catalog(root):
    path = exit0_dir(root) / "course" / "catalog.json"
```
with:
```python
def read_catalog(root):
    path = content_dir(root) / "catalog.json"
```

Replace:
```python
def content_task_dir(root, task_id):
    return exit0_dir(root) / "course" / "tasks" / task_id.lower()
```
with:
```python
def content_task_dir(root, task_id):
    return content_dir(root) / "tasks" / task_id.lower()
```

- [ ] **Step 3: Update `read_task_rules`**

Replace the two `candidate` paths inside `read_task_rules`:
```python
    for candidate in (
        exit0_dir(root) / "course" / "rules.md",
        content_task_dir(root, task_id) / "rules.md",
    ):
```
with:
```python
    for candidate in (
        content_dir(root) / "rules.md",
        content_task_dir(root, task_id) / "rules.md",
    ):
```

- [ ] **Step 4: Update `cmd_read`**

Replace:
```python
    index = exit0_dir(root) / "course" / "knowledgebase" / "index.json"
    location = f".exit0/course/knowledgebase/{topic}/tutorial.md" if topic else None
```
with:
```python
    index = content_dir(root) / "knowledgebase" / "index.json"
    location = f".exit0/content/knowledgebase/{topic}/tutorial.md" if topic else None
```

- [ ] **Step 5: Remove dead functions and constants**

Delete these functions and constants entirely from `cli/bin/e0`:
- `EXIT0_README` (the multiline string constant)
- `DEFAULT_FRAMEWORK_DIR = ".exit0/framework"`
- `read_exit0_json(root)`
- `course_repo_url(root)`
- `framework_path(root)`
- `_version_tuple(value)`
- `e0_supports(requirement)`
- `latest_tag(url)`
- `fetch_course(root, url, tag)`
- `install_skills(root)`

- [ ] **Step 6: Replace `cmd_init`**

Replace the entire body of `cmd_init` with:

```python
def cmd_init(args):
    root, failure = require_repo("init")
    if failure:
        return failure

    if not (content_dir(root) / "catalog.json").exists():
        return problem(
            "init",
            "The course content is not set up yet.",
            "Run: git submodule update --init --recursive",
        )

    profile = read_profile(root) or detect_profile(root)
    write_profile(root, profile)

    catalog = read_catalog(root)
    course = catalog.get("course", {}) if catalog else {}
    (exit0_dir(root) / "tasks").mkdir(parents=True, exist_ok=True)
    append_event(root, "initialized", course=course.get("id"))

    return ok(
        "init",
        {
            "course": course,
            "profile": profile,
            "taskCount": len(catalog.get("tasks", [])) if catalog else 0,
        },
        f"Ready. {course.get('title', 'The course')} has "
        f"{len(catalog.get('tasks', [])) if catalog else 0} tasks.",
    )
```

- [ ] **Step 7: Update `cmd_status` — remove update check**

In `cmd_status`, replace:
```python
    pinned = catalog.get("contentTag")
    available = latest_tag(course_repo_url(root) or "")
    if available is None:
        update = "unknown"
    elif available != pinned:
        update = "available"
    else:
        update = "current"
```
with:
```python
    pinned = catalog.get("contentTag")
    update = "unknown"
```

Also update the `ok(...)` return to remove `"latestTag": available` from the data dict (keep `"contentTag": pinned` and `"update": update`).

- [ ] **Step 8: Verify the file runs without import errors**

```bash
cd /home/alon/Documents/e0
python cli/bin/e0 help
```
Expected: JSON output with `"ok": true` and a list of commands. No stack trace.

- [ ] **Step 9: Commit**

```bash
git add cli/bin/e0
git commit -m "refactor: replace clone-at-init with submodule paths in e0"
```

---

## Task 2: Rewrite `cli/tests/conftest.py` — submodule fixtures

**Files:**
- Rewrite: `cli/tests/conftest.py`

**Interfaces:**
- Removes: `framework_dir` fixture, `FRAMEWORK_DIR` constant
- Adds: `framework_repo` fixture → `Path` to a committed git repo with `bin/e0`, `skills/`, `.gitignore`
- Changes: `student_repo` fixture now depends on `framework_repo` and `content_repo` and wires them as submodules
- Changes: `make_course_repo` no longer tags the repo (no `latest_tag` needed)
- Changes: `content_repo` — same factory, just no tag
- Keeps: `e0mod`, `run_e0`, `make_course_repo`, `_git` helpers unchanged in signature

- [ ] **Step 1: Write the new `conftest.py`**

Replace `cli/tests/conftest.py` entirely with:

```python
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

FIXTURE_COURSE = pathlib.Path(__file__).resolve().parent.parent.parent / "courses" / "demo" / "content"
FRAMEWORK_SRC = pathlib.Path(__file__).resolve().parents[1]  # cli/

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
        return repo

    return _make


@pytest.fixture
def content_repo(make_course_repo):
    """A git repo holding the fixture course content."""
    return make_course_repo()


@pytest.fixture
def framework_repo(tmp_path):
    """Minimal framework git repo matching the .exit0/e0/ expected layout."""
    repo = tmp_path / "framework-repo"
    (repo / "bin").mkdir(parents=True)
    shutil.copy2(E0_PATH, repo / "bin" / "e0")
    skills_src = FRAMEWORK_SRC / "skills"
    if skills_src.is_dir():
        shutil.copytree(skills_src, repo / "skills")
    else:
        (repo / "skills").mkdir()
    # state/ is written at runtime; gitignore it so this submodule stays clean
    (repo / ".gitignore").write_text("state/\n", encoding="utf-8")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture framework")
    return repo


@pytest.fixture
def student_repo(tmp_path, framework_repo, content_repo):
    """A git repo with .exit0/e0 and .exit0/content wired as submodules."""
    repo = tmp_path / "student-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# My course work\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".exit0/e0/state/\n.exit0/tasks/\n", encoding="utf-8")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "initial")
    _git(repo, "submodule", "add", str(framework_repo), ".exit0/e0")
    _git(repo, "submodule", "add", str(content_repo), ".exit0/content")
    _git(repo, "commit", "-q", "-m", "add submodules")
    return repo


@pytest.fixture
def bare_student_repo(tmp_path):
    """A git repo with no submodules — simulates a clone without --recurse-submodules."""
    repo = tmp_path / "bare-student"
    repo.mkdir()
    (repo / "README.md").write_text("# My course work\n", encoding="utf-8")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "initial")
    return repo
```

- [ ] **Step 2: Run the full suite to see what breaks**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest -x -q 2>&1 | head -60
```
Expected: failures in tests that still pass `env={"E0_CONTENT_REPO": ...}` — those are fixed in Task 3.

- [ ] **Step 3: Commit conftest**

```bash
git add cli/tests/conftest.py
git commit -m "test: rewrite fixtures for submodule layout"
```

---

## Task 3: Update all test files — remove env vars and obsolete tests

**Files:**
- Rewrite: `cli/tests/test_init.py`
- Modify: `cli/tests/test_status.py`
- Modify: `cli/tests/test_catalog.py`
- Modify: `cli/tests/test_start.py`
- Modify: `cli/tests/test_check.py`
- Modify: `cli/tests/test_verify.py`
- Modify: `cli/tests/test_skills.py`
- Modify: `cli/tests/test_end_to_end.py`

**Interfaces:**
- All `initialized` and `started` local fixtures drop `content_repo` parameter and env var
- Tests that tested removed features (latest_tag, exit0.json, install_skills, version gate) are deleted and replaced with submodule equivalents

- [ ] **Step 1: Rewrite `test_init.py`**

Replace `cli/tests/test_init.py` entirely:

```python
import json
import subprocess


def test_init_writes_profile_and_creates_tasks_dir(run_e0, student_repo):
    payload, code = run_e0(["init"], student_repo)

    assert code == 0
    assert payload["ok"] is True
    assert (student_repo / ".exit0" / "e0" / "state" / "profile.json").exists()
    assert (student_repo / ".exit0" / "tasks").is_dir()


def test_init_reports_course_title_and_task_count(run_e0, student_repo):
    payload, _ = run_e0(["init"], student_repo)
    assert payload["data"]["course"]["title"] == "Demo Course"
    assert payload["data"]["taskCount"] == 2


def test_init_when_submodule_not_initialized_gives_guidance(run_e0, bare_student_repo):
    payload, code = run_e0(["init"], bare_student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "submodule" in payload["guidance"].lower()


def test_init_is_idempotent(run_e0, student_repo):
    first, _ = run_e0(["init"], student_repo)
    second, code = run_e0(["init"], student_repo)
    assert code == 0
    assert second["ok"] is True
    assert first["data"]["taskCount"] == second["data"]["taskCount"]


def test_init_records_an_event(run_e0, student_repo, e0mod):
    run_e0(["init"], student_repo)
    events = e0mod.read_events(student_repo)
    assert any(event["event"] == "initialized" for event in events)


def test_init_outside_a_git_repo_gives_guidance(run_e0, tmp_path):
    empty = tmp_path / "not-a-repo"
    empty.mkdir()
    payload, code = run_e0(["init"], empty)
    assert code == 0
    assert payload["ok"] is False
    assert payload["guidance"]
```

- [ ] **Step 2: Run init tests**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest tests/test_init.py -v
```
Expected: all 6 tests pass.

- [ ] **Step 3: Update `test_status.py`**

Replace the `initialized` fixture and the two update-check tests:

```python
@pytest.fixture
def initialized(run_e0, student_repo):
    run_e0(["init"], student_repo)
    return student_repo
```

Remove `test_status_reports_update_availability_as_a_string` and `test_status_says_unknown_when_the_course_repo_is_unreachable` entirely.

Replace `test_status_before_init_gives_guidance` with:
```python
def test_status_without_content_gives_guidance(run_e0, bare_student_repo):
    payload, code = run_e0(["status"], bare_student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "init" in payload["guidance"]
```

Remove unused `content_repo` import from the fixture signature. Remove the `import pytest` if no more fixtures use it (check: `initialized` is still a fixture, so keep `pytest`).

- [ ] **Step 4: Update `test_catalog.py`**

Replace `initialized` fixture:
```python
@pytest.fixture
def initialized(run_e0, student_repo):
    run_e0(["init"], student_repo)
    return student_repo
```

Replace `test_catalog_before_init_gives_guidance` to use `bare_student_repo`:
```python
def test_catalog_before_init_gives_guidance(run_e0, bare_student_repo):
    payload, code = run_e0(["catalog"], bare_student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "init" in payload["guidance"]
```

- [ ] **Step 5: Update `test_start.py`**

Replace `initialized` fixture (drop `content_repo` and env):
```python
@pytest.fixture
def initialized(run_e0, student_repo):
    run_e0(["init"], student_repo)
    return student_repo
```

- [ ] **Step 6: Update `test_check.py`**

Replace `started` fixture (drop `content_repo` and env):
```python
@pytest.fixture
def started(run_e0, student_repo):
    run_e0(["init"], student_repo)
    run_e0(["start", "T010"], student_repo)
    return student_repo
```

- [ ] **Step 7: Update `test_verify.py`**

All three setup calls look like:
```python
run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
```
Replace each with:
```python
run_e0(["init"], student_repo)
```
Remove `content_repo` from each test's parameter list.

- [ ] **Step 8: Update `test_skills.py`**

Delete `test_init_installs_framework_skills_and_layers_course_skills` entirely (the function and its imports of `content_repo` and `framework_dir`). Keep all other tests in the file.

- [ ] **Step 9: Update `test_end_to_end.py`**

In `test_a_student_can_go_from_fork_to_passing_checks`:
- Remove `content_repo` from the parameter list
- Remove `env = {"E0_CONTENT_REPO": str(content_repo)}`
- Remove all `env=env` keyword arguments from every `run_e0` call in that test

In `test_pedagogical_drift_is_caught_and_reverted`:
- Remove `content_repo` from the parameter list
- Remove `env = {"E0_CONTENT_REPO": str(content_repo)}`
- Remove `env=env` from `run_e0(["init"], ...)` and `run_e0(["start", ...])` calls

`test_every_command_survives_a_hostile_environment` uses `tmp_path` (not `student_repo`), so no change needed there.

- [ ] **Step 10: Run the full suite**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest -v 2>&1 | tail -30
```
Expected: all tests pass.

- [ ] **Step 11: Commit**

```bash
git add cli/tests/
git commit -m "test: update tests for submodule layout; remove env-var overrides"
```

---

## Task 4: Add pytest-cov and fill coverage gaps

**Files:**
- Modify: `cli/pytest.ini`
- Modify: `cli/tests/test_init.py` (add any gap-filling tests found)
- Modify: `cli/tests/test_end_to_end.py` (add hostile-environment gap tests if any)

**Interfaces:**
- Consumes: working test suite from Task 3
- Produces: coverage report with no uncovered error branches in `cmd_init`, `cmd_status`, `cmd_catalog`, `cmd_start`, `cmd_check`

- [ ] **Step 1: Install pytest-cov**

```bash
pip install pytest-cov
```

- [ ] **Step 2: Add coverage to pytest.ini**

In `cli/pytest.ini`, change `addopts`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = --ignore=tests/fixtures --cov=bin/e0 --cov-report=term-missing
```

Note: `--cov=bin/e0` tells pytest-cov to measure the single-file script at `bin/e0`.

- [ ] **Step 3: Run with coverage and read the report**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest -q 2>&1 | grep -A 40 "TOTAL\|bin/e0"
```
Read the missing-lines column and identify uncovered branches.

- [ ] **Step 4: Add tests for any uncovered error paths**

For each missing branch found in step 3, add a test. Common candidates after the rewrite:

**`cmd_start` with no task id:**
```python
def test_start_without_task_id_gives_guidance(run_e0, initialized):
    payload, code = run_e0(["start"], initialized)
    assert code == 0
    assert payload["ok"] is False
    assert "e0 start" in payload["guidance"]
```

**`cmd_start` with unknown task id:**
```python
def test_start_with_unknown_task_id_gives_guidance(run_e0, initialized):
    payload, code = run_e0(["start", "NOPE"], initialized)
    assert code == 0
    assert payload["ok"] is False
    assert "NOPE" in payload["problem"]
```

**`cmd_profile set` with missing arguments:**
```python
def test_profile_set_without_arguments_gives_guidance(run_e0, student_repo):
    payload, code = run_e0(["profile", "set"], student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "key" in payload["guidance"].lower() or "value" in payload["guidance"].lower()
```

**`cmd_check` before start:**
```python
def test_check_before_start_gives_guidance(run_e0, initialized):
    payload, code = run_e0(["check"], initialized)
    assert code == 0
    assert payload["ok"] is False
    assert payload["guidance"]
```

Add these tests to the appropriate test files (`test_start.py`, `test_check.py`, `test_init.py`, `test_state.py`).

- [ ] **Step 5: Re-run coverage until no critical branches are uncovered**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest -q
```
Expected: all tests pass. Coverage report shows no uncovered lines in the command handlers (`cmd_init`, `cmd_status`, `cmd_catalog`, `cmd_start`, `cmd_check`, `cmd_verify`, `cmd_profile`, `cmd_read`).

- [ ] **Step 6: Delete `courses/demo/template-repo/exit0.json`**

```bash
git rm courses/demo/template-repo/exit0.json
```
The file's content is now superseded by `.gitmodules` entries in real template repos. The demo template repo itself would be updated separately when the GitHub repos exist.

- [ ] **Step 7: Final commit**

```bash
git add cli/pytest.ini cli/tests/ courses/
git commit -m "test: add pytest-cov; fill coverage gaps; remove exit0.json from demo template"
```

---

## Self-Review

**Spec coverage check:**
- ✅ `.exit0/e0/` + `.exit0/content/` as submodules — covered in file map and Task 1 path constants
- ✅ `e0 init` becomes minimal (check submodule, detect OS, write profile) — Task 1 Step 6
- ✅ Dead functions removed — Task 1 Step 5
- ✅ `cmd_status` no longer calls `latest_tag` — Task 1 Step 7
- ✅ Test fixtures rewritten for submodule layout — Task 2
- ✅ All `E0_CONTENT_REPO` / `E0_FRAMEWORK_DIR` references removed — Task 3
- ✅ `exit0.json` deleted from demo template — Task 4 Step 6
- ✅ Coverage tooling added — Task 4

**Placeholder scan:** None found.

**Type consistency:** `content_dir(root)` is introduced in Task 1 Step 1 and consumed by `read_catalog`, `content_task_dir`, `read_task_rules`, `cmd_read` — all in the same file. `state_dir(root)` new path is used by `write_profile`, `append_event`, `read_events`, `read_profile` — all pre-existing callers, no name change.
