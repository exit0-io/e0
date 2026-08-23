# Curl-Bootstrap Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the git-submodule layout with a curl-bootstrap approach — template ships `.exit0/config.json`, `e0 init` fetches everything via HTTP, canonical task content is returned in the JSON envelope (never cached), personalized tasks land in `content/`, checks in `tests/school-checks/`.

**Architecture:** `e0` gains `fetch_text(url)` and two URL-construction helpers that read `config.json`. `cmd_init` fetches catalog + skills over HTTP. `cmd_start` fetches canonical task text and returns it in the JSON envelope; downloads check files to `tests/school-checks/{id}/`. `cmd_verify` re-fetches the canonical, checks that all fixed-region text is present verbatim in the clean personalized `content/{id}/task.md`. Tests use Python's stdlib `http.server` to serve fixture course content and framework skills locally, with URLs injected via `config.json` test-only override keys.

**Tech Stack:** Python 3 stdlib only (`urllib.request`, `http.server`, `threading`), pytest.

## Global Constraints

- `e0` remains a single-file Python 3 script, stdlib only, never crashes, always exits 0.
- JSON envelope shape unchanged: `ok`/`problem` with `command`, `data`, `message`, `guidance`.
- No `E0_CONTENT_REPO`, `E0_FRAMEWORK_DIR` env vars anywhere after this plan.
- State at `.exit0/state/`. Catalog at `.exit0/catalog.json`. Skills at `.exit0/skills/`.
- Personalized task files land at `content/{task_id_lower}/task.md` (gitignored, not `.exit0/`).
- Check files land at `tests/school-checks/{task_id_lower}/` (gitignored).
- Plain, respectful language in all user-facing strings.

---

## File Map

| File | Action |
|---|---|
| `cli/bin/e0` | Modify — new fetch helpers, path updates, rewrite four commands, remove dead code |
| `courses/demo/content/catalog.json` | Modify — remove `contentTag`/`requiresE0`; add `"skills"` list |
| `cli/tests/conftest.py` | Rewrite — HTTP server fixtures replace submodule fixtures |
| `cli/tests/test_init.py` | Rewrite — new init behaviour, HTTP fetch |
| `cli/tests/test_verify.py` | Rewrite — new fixed-chunk verify algorithm |
| `cli/tests/test_start.py` | Rewrite — canonical in envelope, checks in school-checks/ |
| `cli/tests/test_check.py` | Modify — checks path is now `tests/school-checks/{id}/` |
| `cli/tests/test_end_to_end.py` | Rewrite — new task flow |
| `cli/tests/test_status.py` | Modify — drop `bare_student_repo`, use pre-init `student_repo` |
| `cli/tests/test_catalog.py` | No change — fixture already correct after conftest rewrite |
| `cli/tests/test_state.py` | Modify — `state_dir` path assertion |
| `cli/tests/test_template.py` | Rewrite — config.json instead of exit0.json, new AGENTS.md assertions |
| `courses/demo/template/AGENTS.md` | Rewrite |
| `courses/demo/template/.exit0/config.json` | Create |
| `courses/demo/template/.gitignore` | Update |
| `courses/demo/template/.gitmodules` | Delete |

---

## Task 1: Update `cli/bin/e0` — fetch helpers, paths, init, start, verify, check, read

**Files:**
- Modify: `cli/bin/e0`
- Modify: `courses/demo/content/catalog.json`

**Interfaces produced:**
- `read_config(root)` → `dict` — reads `.exit0/config.json`
- `raw_content_url(config, path)` → `str`
- `raw_framework_url(config, path)` → `str`
- `fetch_text(url)` → `str | None`
- `state_dir(root)` → `.exit0/state/` (was `.exit0/e0/state/`)
- `task_content_dir(root, task_id)` → `content/{id_lower}/`
- `school_checks_dir(root, task_id)` → `tests/school-checks/{id_lower}/`
- `download_checks(root, task_id, config)` → `{"copied": [...], "mismatched": []}`
- `verify_document(canonical_text, personalized_text)` → `{"violations": [...]}`  *(no `restored` key)*
- `FRAMEWORK_SKILLS` list constant

**Interfaces removed:**
- `content_dir`, `content_task_dir`, `DEFAULT_FRAMEWORK_DIR`, `EXIT0_README`
- `read_exit0_json`, `course_repo_url`, `framework_path`
- `latest_tag`, `fetch_course`, `install_skills`
- `e0_supports`, `_version_tuple`
- `copy_checks` (replaced by `download_checks`)

---

- [ ] **Step 1: Fix `state_dir`, remove `content_dir`, add `task_content_dir` and `school_checks_dir`**

In `cli/bin/e0`, replace the path-helpers block:

```python
def content_dir(root):
    return exit0_dir(root) / "content"


def state_dir(root):
    return exit0_dir(root) / "e0" / "state"
```

with:

```python
def state_dir(root):
    return exit0_dir(root) / "state"


def task_content_dir(root, task_id):
    return pathlib.Path(root) / "content" / str(task_id).lower()


def school_checks_dir(root, task_id):
    return pathlib.Path(root) / "tests" / "school-checks" / str(task_id).lower()
```

- [ ] **Step 2: Update `read_catalog` to use `.exit0/catalog.json`**

Replace:

```python
def read_catalog(root):
    path = content_dir(root) / "catalog.json"
```

with:

```python
def read_catalog(root):
    path = exit0_dir(root) / "catalog.json"
```

- [ ] **Step 3: Add `read_config`, URL helpers, `fetch_text`, and `FRAMEWORK_SKILLS`**

Add after the existing `require_repo` function:

```python
FRAMEWORK_SKILLS = ["session.md", "working-on-a-task.md", "using-the-knowledge-base.md"]


def read_config(root):
    path = exit0_dir(root) / "config.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def raw_content_url(config, path):
    """URL for a file in the course content repo."""
    base = config.get("_rawContentBase", "").rstrip("/")
    if base:
        return f"{base}/{path}"
    repo = config.get("courseContentRepo", "")
    return f"https://raw.githubusercontent.com/{repo}/main/{path}"


def raw_framework_url(config, path):
    """URL for a file in the e0 framework repo."""
    base = config.get("_rawFrameworkBase", "").rstrip("/")
    if base:
        return f"{base}/{path}"
    return f"https://raw.githubusercontent.com/exit0-io/e0/{E0_VERSION}/cli/{path}"


def fetch_text(url):
    """Fetch a URL and return its text body, or None on any error."""
    import urllib.request
    import urllib.error
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except Exception:  # noqa: BLE001
        return None
```

- [ ] **Step 4: Rewrite `cmd_init`**

Replace the entire body of `cmd_init`:

```python
def cmd_init(args):
    root, failure = require_repo("init")
    if failure:
        return failure

    config = read_config(root)
    if not config.get("courseContentRepo"):
        return problem(
            "init",
            "e0 cannot find the course content repo.",
            "Check that .exit0/config.json exists and has a 'courseContentRepo' key.",
        )

    catalog_text = fetch_text(raw_content_url(config, "catalog.json"))
    if catalog_text is None:
        return problem(
            "init",
            "e0 could not download the course catalog.",
            "Check your internet connection and the 'courseContentRepo' in .exit0/config.json.",
        )

    try:
        catalog = json.loads(catalog_text)
    except ValueError:
        return problem(
            "init",
            "The course catalog is not valid JSON.",
            "This is a problem with the course itself. Please report it.",
        )

    (exit0_dir(root) / "catalog.json").write_text(catalog_text, encoding="utf-8")

    # Framework skills
    skills_dir = exit0_dir(root) / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    for name in FRAMEWORK_SKILLS:
        text = fetch_text(raw_framework_url(config, f"skills/{name}"))
        if text is not None:
            (skills_dir / name).write_text(text, encoding="utf-8")

    # Course skills (layered on top)
    for name in catalog.get("skills", []):
        text = fetch_text(raw_content_url(config, f"skills/{name}"))
        if text is not None:
            (skills_dir / name).write_text(text, encoding="utf-8")

    profile = read_profile(root) or detect_profile(root)
    write_profile(root, profile)

    (pathlib.Path(root) / "content").mkdir(exist_ok=True)
    (pathlib.Path(root) / "tests" / "school-checks").mkdir(parents=True, exist_ok=True)

    course = catalog.get("course", {})
    append_event(root, "initialized", course=course.get("id"))

    return ok(
        "init",
        {
            "course": course,
            "profile": profile,
            "taskCount": len(catalog.get("tasks", [])),
        },
        f"Ready. {course.get('title', 'The course')} has "
        f"{len(catalog.get('tasks', []))} tasks.",
    )
```

- [ ] **Step 5: Rewrite `cmd_start` — fetch canonical + download checks**

Replace the entire body of `cmd_start`. First add a helper `download_checks` above `cmd_start`:

```python
def download_checks(root, task_id, config):
    """Fetch checks.json and all listed check files into tests/school-checks/{id}/."""
    import shutil
    dest = school_checks_dir(root, task_id)
    result = {"copied": [], "mismatched": []}

    checks_text = fetch_text(raw_content_url(config, f"tasks/{task_id.lower()}/checks/checks.json"))
    if checks_text is None:
        return result

    try:
        spec = json.loads(checks_text)
    except ValueError:
        return result

    dest.mkdir(parents=True, exist_ok=True)
    (dest / "checks.json").write_text(checks_text, encoding="utf-8")
    result["copied"].append("checks.json")

    for name in spec.get("files", {}):
        file_text = fetch_text(raw_content_url(config, f"tasks/{task_id.lower()}/checks/{name}"))
        if file_text is not None:
            (dest / name).write_text(file_text, encoding="utf-8")
            result["copied"].append(name)
            if sha256_file(dest / name) != spec["files"][name]:
                result["mismatched"].append(name)

    return result
```

Then replace `cmd_start` body:

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
            f"Use: e0 start <id>. The tasks you can start are: {available}",
        )

    task = find_task(catalog, args[0])
    if task is None:
        available = ", ".join(item["id"] for item in catalog.get("tasks", []))
        return problem(
            "start",
            f"There is no task called '{args[0]}'.",
            f"The tasks you can start are: {available}",
        )

    task_id = task["id"]
    config = read_config(root)

    canonical_text = fetch_text(raw_content_url(config, f"tasks/{task_id.lower()}/task.md"))
    if canonical_text is None:
        return problem(
            "start",
            f"e0 could not download task {task_id}.",
            "Check your internet connection.",
        )

    checks = download_checks(root, task_id, config)

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
                    "You can keep going, but you might be missing important background."
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
                "message": f"The personalization markers in this task have a problem ({exc}). "
                "The task text is still correct. It just won't be personalized for you.",
            }
        )

    append_event(root, "task_started", taskId=task_id)

    task_dir = task_content_dir(root, task_id)
    body = (
        f"{task.get('description', '')}\n\n"
        f"Working through **{task['title']}**.\n\n"
        f"Write the personalized task to: `content/{task_id.lower()}/task.md`"
    ).strip()

    return ok(
        "start",
        {
            "taskId": task_id,
            "title": task["title"],
            "canonical": canonical_text,
            "paths": {
                "task": f"content/{task_id.lower()}/task.md",
                "checks": f"tests/school-checks/{task_id.lower()}",
            },
            "relatedTopics": task.get("relatedTopics", []),
            "warnings": warnings,
            "personalization": payload,
            "markerProblem": marker_problem,
            "issue": {"title": f"[{task_id}] {task['title']}", "body": body},
        },
        f"Canonical text for {task_id} is in data.canonical. "
        f"Personalize it and write to content/{task_id.lower()}/task.md, "
        f"then run e0 verify {task_id}.",
    )
```

- [ ] **Step 6: Rewrite `verify_document` — fixed-chunk algorithm**

Replace the entire `verify_document` function:

```python
def verify_document(canonical_text, personalized_text):
    """Check that all fixed regions from canonical are intact in the clean personalized doc.

    The personalized doc is clean Markdown with no markers. Returns {"violations": [...]}.
    """
    try:
        regions = parse_regions(canonical_text)
    except MarkerError as exc:
        return {
            "violations": [
                {
                    "kind": "structure",
                    "message": f"The original document has markers with a problem: {exc}",
                }
            ]
        }

    violations = []
    for region in regions:
        if region["kind"] == "fixed" and region["text"].strip():
            if region["text"] not in personalized_text:
                violations.append(
                    {
                        "kind": "fixed",
                        "message": "Protected text was changed or removed. "
                                   "Re-personalize from the canonical in data.canonical.",
                    }
                )
    return {"violations": violations}
```

- [ ] **Step 7: Rewrite `cmd_verify` — re-fetch canonical, no restore**

Replace the entire body of `cmd_verify`:

```python
def cmd_verify(args):
    root, failure = require_repo("verify")
    if failure:
        return failure

    if not args:
        return problem(
            "verify",
            "e0 verify needs a task id.",
            "Use: e0 verify <taskId>",
        )

    catalog, failure = require_content("verify", root)
    if failure:
        return failure

    task = find_task(catalog, args[0])
    if task is None:
        return problem(
            "verify",
            f"There is no task called '{args[0]}'.",
            "Run 'e0 catalog' to see the task ids.",
        )

    task_id = task["id"]
    config = read_config(root)

    canonical_text = fetch_text(raw_content_url(config, f"tasks/{task_id.lower()}/task.md"))
    if canonical_text is None:
        return problem(
            "verify",
            f"e0 could not download the canonical task for {task_id}.",
            "Check your internet connection.",
        )

    personalized_path = task_content_dir(root, task_id) / "task.md"
    if not personalized_path.exists():
        return problem(
            "verify",
            f"The personalized task for {task_id} does not exist yet.",
            f"Personalize the canonical text from 'e0 start {task_id}' "
            f"and write it to content/{task_id.lower()}/task.md.",
        )

    result = verify_document(canonical_text, personalized_path.read_text(encoding="utf-8"))

    if not result["violations"]:
        return ok(
            "verify",
            {"violations": [], "path": f"content/{task_id.lower()}/task.md"},
            "Your personalization follows the rules.",
        )

    append_event(
        root, "verify_failed", taskId=task_id, count=len(result["violations"])
    )
    payload = problem(
        "verify",
        "The personalized task changed text it is not allowed to change. "
        + " ".join(v["message"] for v in result["violations"]),
        f"Re-personalize from the canonical text returned by 'e0 start {task_id}'.",
    )
    payload["data"] = {"violations": result["violations"]}
    return payload
```

- [ ] **Step 8: Rewrite `cmd_read` — fetch tutorial and return in envelope**

Replace the entire body of `cmd_read`:

```python
def cmd_read(args):
    root, failure = require_repo("read")
    if failure:
        return failure

    if not args:
        catalog, failure = require_content("read", root)
        if failure:
            return failure
        config = read_config(root)
        index_text = fetch_text(raw_content_url(config, "knowledgebase/index.json"))
        topics = []
        if index_text:
            try:
                topics = json.loads(index_text).get("topics", [])
            except ValueError:
                pass
        return ok(
            "read",
            {"topics": topics},
            "Use 'e0 read <topic>' to read a knowledge base tutorial.",
        )

    topic = args[0]
    catalog, failure = require_content("read", root)
    if failure:
        return failure

    config = read_config(root)
    tutorial_text = fetch_text(
        raw_content_url(config, f"knowledgebase/{topic}/tutorial.md")
    )
    if tutorial_text is None:
        return problem(
            "read",
            f"e0 could not download the tutorial for '{topic}'.",
            "Run 'e0 read' (no topic) to see available topics.",
        )

    return ok(
        "read",
        {
            "topic": topic,
            "tutorial": tutorial_text,
            "suggestedPath": f"content/knowledge-base/{topic}.md",
        },
        f"Tutorial for '{topic}' is in data.tutorial. "
        f"You can write it to content/knowledge-base/{topic}.md if the student wants a local copy.",
    )
```

- [ ] **Step 9: Update `cmd_check` — checks path is now `school_checks_dir`**

Replace:
```python
def read_checks_spec(root, task_id):
    path = task_dir(root, task_id) / "checks" / "checks.json"
```
with:
```python
def read_checks_spec(root, task_id):
    path = school_checks_dir(root, task_id) / "checks.json"
```

Replace:
```python
def check_hashes(root, task_id):
    """Names of check files whose contents no longer match checks.json."""
    spec = read_checks_spec(root, task_id)
    if not spec:
        return []
    checks = task_dir(root, task_id) / "checks"
```
with:
```python
def check_hashes(root, task_id):
    """Names of check files whose contents no longer match checks.json."""
    spec = read_checks_spec(root, task_id)
    if not spec:
        return []
    checks = school_checks_dir(root, task_id)
```

Replace in `run_checks`:
```python
    checks = task_dir(root, task_id) / "checks"
```
with:
```python
    checks = school_checks_dir(root, task_id)
```

In `cmd_check`, replace the "not downloaded yet" check:
```python
    if not (task_dir(root, task_id) / "checks").exists():
        return problem(
            "check",
            f"The checks for {task_id} have not been downloaded yet.",
            f"Run 'e0 start {task_id}' first.",
        )
```
with:
```python
    if not school_checks_dir(root, task_id).exists():
        return problem(
            "check",
            f"The checks for {task_id} have not been downloaded yet.",
            f"Run 'e0 start {task_id}' first.",
        )
```

- [ ] **Step 10: Remove dead functions**

Delete these entirely from `cli/bin/e0`:
- `EXIT0_README` (multiline string constant)
- `DEFAULT_FRAMEWORK_DIR = ".exit0/framework"` (if still present)
- `read_exit0_json(root)`
- `course_repo_url(root)`
- `framework_path(root)`
- `_version_tuple(value)`
- `e0_supports(requirement)`
- `latest_tag(url)`
- `fetch_course(root, url, tag)`
- `install_skills(root)`
- `copy_checks(root, task_id)` (replaced by `download_checks`)
- `read_task_rules(root, task_id)` (deferred to review feature)
- `_maybe_decode(raw)` (used only by `read_task_rules`)
- `task_dir(root, task_id)` (replaced by `task_content_dir` and `school_checks_dir`)

Also remove the `"rules"` field from `cmd_start`'s return data if any reference was left.

- [ ] **Step 11: Update `courses/demo/content/catalog.json`**

Remove `contentTag` and `requiresE0`. Add `"skills"` list:

```json
{
  "course": {
    "id": "demo",
    "title": "Demo Course",
    "feedbackRepo": "exit0-io/feedback"
  },
  "skills": ["demo-course-notes.md"],
  "tasks": [...]
}
```

- [ ] **Step 12: Verify no syntax errors**

```bash
cd /home/alon/Documents/e0
python cli/bin/e0 help
```
Expected: JSON output with `"ok": true` and a list of commands. No stack trace.

- [ ] **Step 13: Commit**

```bash
git add cli/bin/e0 courses/demo/content/catalog.json
git commit -m "refactor: curl-bootstrap layout — fetch helpers, HTTP init/start/verify/read"
```

---

## Task 2: Rewrite `cli/tests/conftest.py` — HTTP server fixtures

**Files:**
- Rewrite: `cli/tests/conftest.py`

**Interfaces produced:**
- `content_server` fixture → `str` (base URL, e.g. `http://127.0.0.1:PORT`)
- `framework_server` fixture → `str`
- `student_repo` fixture → `Path` (git repo with `.exit0/config.json` pointing to local servers)
- `make_course_dir` fixture → factory returning `Path` to a temp copy of the fixture course
- `run_e0` fixture — unchanged signature
- `e0mod` fixture — unchanged
- Removed: `framework_repo`, `content_repo`, `bare_student_repo`, `framework_dir`, `make_course_repo`

---

- [ ] **Step 1: Write the new `conftest.py`**

Replace `cli/tests/conftest.py` entirely:

```python
import functools
import http.server
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import threading

import pytest

FIXTURE_COURSE = pathlib.Path(__file__).resolve().parents[2] / "courses" / "demo" / "content"
FRAMEWORK_SRC = pathlib.Path(__file__).resolve().parents[1]   # cli/
E0_PATH = FRAMEWORK_SRC / "bin" / "e0"


def _load_e0():
    loader = importlib.machinery.SourceFileLoader("e0", str(E0_PATH))
    spec = importlib.util.spec_from_loader("e0", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@pytest.fixture
def e0mod():
    return _load_e0()


_COVERAGE_CFG = str(FRAMEWORK_SRC / "setup.cfg")


@pytest.fixture
def run_e0():
    """Invoke e0 as a real subprocess and return (parsed_json, exit_code)."""

    def _run(args, cwd, env=None):
        merged = dict(os.environ)
        merged.update(env or {})
        merged.setdefault("COVERAGE_PROCESS_START", _COVERAGE_CFG)
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
def make_course_dir(tmp_path):
    """Copy the fixture course to a temp dir, optionally mutating catalog.json first."""
    counter = {"n": 0}

    def _make(mutate_catalog=None):
        counter["n"] += 1
        dest = tmp_path / f"course-{counter['n']}"
        shutil.copytree(FIXTURE_COURSE, dest)
        if mutate_catalog is not None:
            p = dest / "catalog.json"
            catalog = json.loads(p.read_text(encoding="utf-8"))
            mutate_catalog(catalog)
            p.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
        return dest

    return _make


def _start_file_server(directory):
    """Start a SimpleHTTPServer on a random free port. Returns (server, base_url)."""

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), QuietHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()
    return server, f"http://127.0.0.1:{port}"


@pytest.fixture
def content_server(make_course_dir):
    """HTTP server serving a temp copy of the fixture course. Returns base URL."""
    course_dir = make_course_dir()
    server, url = _start_file_server(course_dir)
    yield url
    server.shutdown()


@pytest.fixture
def framework_server():
    """HTTP server serving cli/ so skills are at /skills/<name>.md. Returns base URL."""
    server, url = _start_file_server(FRAMEWORK_SRC)
    yield url
    server.shutdown()


@pytest.fixture
def student_repo(tmp_path, content_server, framework_server):
    """Git repo with .exit0/config.json wired to local HTTP servers."""
    repo = tmp_path / "student-repo"
    repo.mkdir()
    (repo / ".exit0").mkdir()
    (repo / ".exit0" / "config.json").write_text(
        json.dumps(
            {
                "courseContentRepo": "exit0-io/demo-content",
                "_rawContentBase": content_server,
                "_rawFrameworkBase": framework_server,
            }
        ),
        encoding="utf-8",
    )
    (repo / ".gitignore").write_text(
        ".exit0/e0\n"
        ".exit0/catalog.json\n"
        ".exit0/skills/\n"
        ".exit0/state/\n"
        "content/\n"
        "tests/school-checks/\n",
        encoding="utf-8",
    )
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "initial")
    return repo
```

- [ ] **Step 2: Run the suite to see which tests fail**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest -x -q 2>&1 | head -60
```
Expected: failures in test files that still reference old paths/fixtures — those are fixed in Task 3.

- [ ] **Step 3: Commit**

```bash
git add cli/tests/conftest.py
git commit -m "test: rewrite conftest for HTTP server fixtures"
```

---

## Task 3: Rewrite `test_init.py`, `test_verify.py`, `test_start.py`; update remaining tests

**Files:**
- Rewrite: `cli/tests/test_init.py`
- Rewrite: `cli/tests/test_verify.py`
- Rewrite: `cli/tests/test_start.py`
- Modify: `cli/tests/test_check.py`
- Modify: `cli/tests/test_status.py`
- Modify: `cli/tests/test_state.py`
- Rewrite: `cli/tests/test_end_to_end.py`

---

- [ ] **Step 1: Rewrite `test_init.py`**

Replace `cli/tests/test_init.py` entirely:

```python
def test_init_downloads_catalog_and_writes_profile(run_e0, student_repo):
    payload, code = run_e0(["init"], student_repo)

    assert code == 0
    assert payload["ok"] is True
    assert (student_repo / ".exit0" / "catalog.json").exists()
    assert (student_repo / ".exit0" / "state" / "profile.json").exists()


def test_init_reports_course_title_and_task_count(run_e0, student_repo):
    payload, _ = run_e0(["init"], student_repo)
    assert payload["data"]["course"]["title"] == "Demo Course"
    assert payload["data"]["taskCount"] == 2


def test_init_installs_framework_skills(run_e0, student_repo):
    run_e0(["init"], student_repo)
    skills = student_repo / ".exit0" / "skills"
    assert (skills / "session.md").exists()
    assert (skills / "working-on-a-task.md").exists()


def test_init_installs_course_skills(run_e0, student_repo):
    run_e0(["init"], student_repo)
    assert (student_repo / ".exit0" / "skills" / "demo-course-notes.md").exists()


def test_init_creates_content_and_school_checks_dirs(run_e0, student_repo):
    run_e0(["init"], student_repo)
    assert (student_repo / "content").is_dir()
    assert (student_repo / "tests" / "school-checks").is_dir()


def test_init_is_idempotent(run_e0, student_repo):
    run_e0(["init"], student_repo)
    payload, code = run_e0(["init"], student_repo)
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["taskCount"] == 2


def test_init_records_an_event(run_e0, student_repo, e0mod):
    run_e0(["init"], student_repo)
    events = e0mod.read_events(student_repo)
    assert any(event["event"] == "initialized" for event in events)


def test_init_without_config_json_gives_guidance(run_e0, tmp_path):
    import subprocess
    bare = tmp_path / "no-config"
    bare.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(bare), check=True)
    (bare / ".exit0").mkdir()
    (bare / ".exit0" / "config.json").write_text("{}", encoding="utf-8")
    payload, code = run_e0(["init"], bare)
    assert code == 0
    assert payload["ok"] is False
    assert "courseContentRepo" in payload["guidance"]


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
Expected: all tests pass.

- [ ] **Step 3: Rewrite `test_verify.py`**

The canonical has markers; the personalized is clean Markdown. Replace entirely:

```python
CANONICAL = """\
# Task

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

# A correctly personalized clean document — no markers, one variant branch selected.
PERSONALIZED_OK = """\
# Task

Build the agent using **langchain**.

brew install ffmpeg

You have done this before, so skim it.

Done.
"""

PERSONALIZED_ALTERED_FIXED = """\
# Task

Build the agent using **langgraph**.

brew install ffmpeg

Done.
"""


def test_clean_personalized_doc_has_no_violations(e0mod):
    result = e0mod.verify_document(CANONICAL, PERSONALIZED_OK)
    assert result["violations"] == []


def test_altering_fixed_prose_is_a_violation(e0mod):
    result = e0mod.verify_document(CANONICAL, PERSONALIZED_ALTERED_FIXED)
    assert any(v["kind"] == "fixed" for v in result["violations"])


def test_missing_fixed_chunk_is_a_violation(e0mod):
    # Remove the "Done." line entirely.
    personalized = PERSONALIZED_OK.replace("Done.\n", "")
    result = e0mod.verify_document(CANONICAL, personalized)
    assert any(v["kind"] == "fixed" for v in result["violations"])


def test_verify_document_returns_no_restored_key(e0mod):
    result = e0mod.verify_document(CANONICAL, PERSONALIZED_OK)
    assert "restored" not in result


def test_malformed_canonical_markers_are_a_structure_violation(e0mod):
    bad_canonical = "<!-- e0:variant id=\"x\" -->\nno closer\n"
    result = e0mod.verify_document(bad_canonical, "anything")
    assert any(v["kind"] == "structure" for v in result["violations"])


def test_cmd_verify_passes_for_correct_personalized_file(run_e0, student_repo, e0mod):
    run_e0(["init"], student_repo)
    start_payload, _ = run_e0(["start", "T010"], student_repo)
    canonical = start_payload["data"]["canonical"]
    # Simulate a minimal clean personalization: strip all markers, keep prose.
    regions = e0mod.parse_regions(canonical)
    clean_parts = []
    for r in regions:
        if r["kind"] == "fixed":
            clean_parts.append(r["text"])
        elif r["kind"] == "variant":
            # Pick first branch text
            clean_parts.append(r["branches"][0]["text"])
        else:
            clean_parts.append("Skim this section.\n")
    task_dir = student_repo / "content" / "t010"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.md").write_text("\n".join(clean_parts), encoding="utf-8")
    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert payload["ok"] is True


def test_cmd_verify_fails_when_fixed_text_is_altered(run_e0, student_repo):
    run_e0(["init"], student_repo)
    start_payload, _ = run_e0(["start", "T010"], student_repo)
    canonical = start_payload["data"]["canonical"]
    # Use canonical as base (has markers), alter a fixed region
    task_dir = student_repo / "content" / "t010"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.md").write_text(
        canonical.replace("**standard library**", "**requests library**"),
        encoding="utf-8",
    )
    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert payload["data"]["violations"]
```

- [ ] **Step 4: Run verify tests**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest tests/test_verify.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Rewrite `test_start.py`**

Replace entirely:

```python
import pytest


@pytest.fixture
def initialized(run_e0, student_repo):
    run_e0(["init"], student_repo)
    return student_repo


def test_start_returns_canonical_text_in_envelope(run_e0, initialized):
    payload, code = run_e0(["start", "T010"], initialized)
    assert code == 0
    assert payload["ok"] is True
    assert isinstance(payload["data"]["canonical"], str)
    assert len(payload["data"]["canonical"]) > 0


def test_start_downloads_check_files_to_school_checks(run_e0, initialized):
    run_e0(["start", "T010"], initialized)
    checks = initialized / "tests" / "school-checks" / "t010"
    assert (checks / "test_greeting.py").exists()
    assert (checks / "checks.json").exists()


def test_start_does_not_write_task_to_exit0(run_e0, initialized):
    run_e0(["start", "T010"], initialized)
    assert not (initialized / ".exit0" / "tasks").exists()


def test_start_reports_task_path_as_content_dir(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    assert payload["data"]["paths"]["task"] == "content/t010/task.md"


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


def test_start_does_not_include_rules_in_envelope(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    assert "rules" not in payload["data"]


def test_start_warns_about_unmet_dependencies_but_proceeds(run_e0, initialized):
    payload, code = run_e0(["start", "T020"], initialized)
    assert code == 0
    assert payload["ok"] is True
    warnings = payload["data"]["warnings"]
    assert any(warning["kind"] == "dependency" for warning in warnings)
```

- [ ] **Step 6: Run start tests**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest tests/test_start.py -v
```
Expected: all pass.

- [ ] **Step 7: Update `test_check.py` — checks path is `tests/school-checks/`**

Replace `started` fixture and update path references:

```python
@pytest.fixture
def started(run_e0, student_repo):
    run_e0(["init"], student_repo)
    run_e0(["start", "T010"], student_repo)
    return student_repo
```

Replace the drift test's path:

```python
def test_check_warns_when_a_test_file_has_drifted(run_e0, started):
    check_file = started / "tests" / "school-checks" / "t010" / "test_greeting.py"
    check_file.write_text("# oops I edited this\n", encoding="utf-8")
    payload, _ = run_e0(["check", "T010"], started)
    assert any(warning["kind"] == "check_hash" for warning in payload["data"]["warnings"])


def test_check_hashes_detects_drift(e0mod, started):
    assert e0mod.check_hashes(started, "T010") == []
    check_file = started / "tests" / "school-checks" / "t010" / "test_greeting.py"
    check_file.write_text("# edited\n", encoding="utf-8")
    assert e0mod.check_hashes(started, "T010") == ["test_greeting.py"]
```

- [ ] **Step 8: Run check tests**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest tests/test_check.py -v
```
Expected: all pass.

- [ ] **Step 9: Update `test_status.py` — drop `bare_student_repo`**

The `bare_student_repo` fixture is gone. The "before init" test should use `student_repo` directly (config.json present, no catalog yet):

Replace `test_status_before_init_gives_guidance`:

```python
def test_status_before_init_gives_guidance(run_e0, student_repo):
    payload, code = run_e0(["status"], student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "init" in payload["guidance"]
```

- [ ] **Step 10: Update `test_state.py` — state_dir path**

The `state_dir` now returns `.exit0/state/`. The test `test_append_and_read_events_roundtrip` and others use `e0mod.state_dir(student_repo)` — that works unchanged. No code change needed; just run to verify:

```bash
cd /home/alon/Documents/e0/cli
python -m pytest tests/test_state.py -v
```
Expected: all pass (state_dir path is now `.exit0/state/`, which is what the fixture's `student_repo` uses after init writes `profile.json` there).

- [ ] **Step 11: Rewrite `test_end_to_end.py`**

Replace entirely:

```python
import subprocess


def test_a_student_can_go_from_bootstrap_to_passing_checks(
    run_e0, student_repo, e0mod
):
    # 1. Agent bootstraps.
    payload, code = run_e0(["init"], student_repo)
    assert code == 0 and payload["ok"] is True
    assert payload["data"]["taskCount"] == 2

    # 2. Agent orients.
    payload, _ = run_e0(["status"], student_repo)
    assert payload["data"]["next"]["id"] == "T010"

    # 3. Student asks what the course covers.
    payload, _ = run_e0(["catalog"], student_repo)
    assert [t["id"] for t in payload["data"]["tasks"]] == ["T010", "T020"]

    # 4. Agent starts the first task.
    payload, _ = run_e0(["start", "T010"], student_repo)
    assert payload["data"]["warnings"] == []
    canonical = payload["data"]["canonical"]
    assert canonical

    # 5. Agent personalizes: strip markers, pick a branch, write clean Markdown.
    regions = e0mod.parse_regions(canonical)
    facts = payload["data"]["personalization"]["facts"]
    clean_parts = []
    for r in regions:
        if r["kind"] == "fixed":
            clean_parts.append(r["text"])
        elif r["kind"] == "variant":
            chosen = e0mod.select_branch(r["branches"], facts)
            clean_parts.append((chosen["text"] if chosen else r["branches"][0]["text"]) + "\n")
        else:
            clean_parts.append("Skim this.\n")
    task_dir = student_repo / "content" / "t010"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.md").write_text("".join(clean_parts), encoding="utf-8")

    # 6. Verify accepts the personalization.
    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0 and payload["ok"] is True

    # 7. Checks fail before any code is written.
    payload, _ = run_e0(["check", "T010"], student_repo)
    assert payload["data"]["passed"] is False

    # 8. Student writes the code.
    (student_repo / "greeting.py").write_text(
        'def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8"
    )

    # 9. Checks pass.
    payload, code = run_e0(["check", "T010"], student_repo)
    assert code == 0 and payload["ok"] is True
    assert payload["data"]["passed"] is True

    # 10. Nothing in .exit0/ leaked into git status.
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(student_repo),
        capture_output=True,
        text=True,
    )
    tracked_changes = [line for line in proc.stdout.splitlines() if ".exit0" in line]
    assert tracked_changes == [], ".exit0/ must never appear in git status"


def test_verify_catches_altered_fixed_text(run_e0, student_repo):
    run_e0(["init"], student_repo)
    start_payload, _ = run_e0(["start", "T010"], student_repo)
    canonical = start_payload["data"]["canonical"]

    # Write a personalized file that alters protected text.
    task_dir = student_repo / "content" / "t010"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.md").write_text(
        canonical.replace("**standard library**", "**the requests library**"),
        encoding="utf-8",
    )

    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert payload["data"]["violations"]


def test_every_command_survives_a_hostile_environment(run_e0, tmp_path):
    """No command may crash, whatever state it is run in."""
    empty = tmp_path / "empty"
    empty.mkdir()
    for command in ["status", "catalog", "start", "verify", "check", "read", "init", "help"]:
        payload, code = run_e0([command], empty)
        assert code == 0, f"{command} must exit 0"
        assert isinstance(payload["ok"], bool), f"{command} must return a bool ok"
```

- [ ] **Step 12: Run the full suite**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest -v 2>&1 | tail -40
```
Expected: all tests pass.

- [ ] **Step 13: Commit**

```bash
git add cli/tests/
git commit -m "test: rewrite tests for HTTP-fetch layout; checks in school-checks/"
```

---

## Task 4: Update the demo template repo and `test_template.py`

**Files:**
- Rewrite: `courses/demo/template/AGENTS.md`
- Create: `courses/demo/template/.exit0/config.json`
- Update: `courses/demo/template/.gitignore`
- Delete: `courses/demo/template/.gitmodules`
- Delete submodule dirs: `courses/demo/template/.exit0/e0/` and `courses/demo/template/.exit0/content/`
- Rewrite: `cli/tests/test_template.py`

---

- [ ] **Step 1: Remove submodule entries**

```bash
cd /home/alon/Documents/e0/courses/demo/template
git rm --cached .exit0/e0 .exit0/content 2>/dev/null || true
rm -rf .exit0/e0 .exit0/content .gitmodules
```

- [ ] **Step 2: Create `.exit0/config.json`**

```bash
mkdir -p courses/demo/template/.exit0
```

Write `courses/demo/template/.exit0/config.json`:

```json
{
  "courseContentRepo": "exit0-io/demo-content"
}
```

- [ ] **Step 3: Update `.gitignore`**

Replace `courses/demo/template/.gitignore` contents:

```
.exit0/e0
.exit0/catalog.json
.exit0/skills/
.exit0/state/
content/
tests/school-checks/
__pycache__/
*.pyc
.venv/
```

- [ ] **Step 4: Rewrite `AGENTS.md`**

Replace `courses/demo/template/AGENTS.md`:

```markdown
# The demo course

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
After init: tell the student to allow `.exit0/e0` to run without confirmation — it drives the course, sends no code anywhere.

## Every session
Read `.exit0/skills/session.md` before anything else.

## Learning cycle
Tasks → GitHub issues. `e0 read <topic>` for knowledge base. Feature branch → PR → review → comp check → close PR = done.

## Course questions
`.exit0/catalog.json` has everything: tasks, technologies, order.

## Skills
All in `.exit0/skills/`. Session skill loads them.

<!-- ================================================================= END EXIT ZERO ================================================================= -->

---
<!-- Add your own project notes below. -->
```

- [ ] **Step 5: Rewrite `test_template.py`**

Replace `cli/tests/test_template.py` entirely:

```python
import json
import pathlib

TEMPLATE = pathlib.Path(__file__).resolve().parents[2] / "courses" / "demo" / "template"


def test_template_has_required_files():
    for name in ("README.md", "AGENTS.md", "CLAUDE.md", ".exit0/config.json", ".gitignore"):
        assert (TEMPLATE / name).exists(), f"missing {name}"


def test_exit0_json_replaced_by_config_json():
    assert not (TEMPLATE / "exit0.json").exists(), "exit0.json must be removed"


def test_config_json_names_course_content_repo():
    config = json.loads((TEMPLATE / ".exit0" / "config.json").read_text(encoding="utf-8"))
    assert "courseContentRepo" in config
    assert "exit0-io" in config["courseContentRepo"]


def test_no_gitmodules_file():
    assert not (TEMPLATE / ".gitmodules").exists(), ".gitmodules must be removed"


def test_no_submodule_dirs():
    assert not (TEMPLATE / ".exit0" / "e0").exists()
    assert not (TEMPLATE / ".exit0" / "content").exists()


def test_gitignore_covers_generated_dirs():
    text = (TEMPLATE / ".gitignore").read_text(encoding="utf-8")
    for entry in ("content/", "tests/school-checks/", ".exit0/catalog.json", ".exit0/skills/"):
        assert entry in text, f".gitignore missing: {entry}"


def test_agents_md_has_curl_bootstrap():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert "curl" in agents
    assert "RELEASE" in agents
    assert ".exit0/e0 init" in agents


def test_agents_md_points_to_session_skill():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert "session.md" in agents


def test_agents_md_has_do_not_modify_marker():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert "DO NOT MODIFY" in agents


def test_readme_tells_the_student_to_say_hi():
    readme = (TEMPLATE / "README.md").read_text(encoding="utf-8").lower()
    assert "hi" in readme


def test_claude_md_redirects_to_agents_md():
    claude = (TEMPLATE / "CLAUDE.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in claude
```

- [ ] **Step 6: Commit the template**

```bash
cd /home/alon/Documents/e0
git add courses/demo/template/
git commit -m "feat: replace submodule layout with curl-bootstrap in demo template"
```

- [ ] **Step 7: Run template tests**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest tests/test_template.py -v
```
Expected: all pass.

- [ ] **Step 8: Run the full suite one final time**

```bash
cd /home/alon/Documents/e0/cli
python -m pytest -v
```
Expected: all tests pass.

- [ ] **Step 9: Final commit**

```bash
git add cli/tests/test_template.py
git commit -m "test: update test_template for curl-bootstrap layout"
```

---

## Self-Review

**Spec coverage:**
- ✅ `.exit0/config.json` committed in template — Task 4 Step 2
- ✅ `curl` bootstrap in `AGENTS.md` — Task 4 Step 4
- ✅ Agent told to recommend auto-allow for `.exit0/e0` — Task 4 Step 4
- ✅ `e0 init` fetches catalog + skills via HTTP — Task 1 Step 4
- ✅ `state_dir` → `.exit0/state/` — Task 1 Step 1
- ✅ Framework + course skills layered — Task 1 Step 4
- ✅ `e0 start` fetches canonical, returns in envelope, downloads checks to `tests/school-checks/` — Task 1 Step 5
- ✅ No rules fetched in `e0 start` — confirmed: `read_task_rules` removed
- ✅ `e0 verify` re-fetches canonical, fixed-chunk check, no restore — Task 1 Steps 6–7
- ✅ `e0 read <topic>` fetches tutorial, returns in envelope — Task 1 Step 8
- ✅ `content/knowledge-base/` name (not `kb/`) — Task 1 Step 8 `suggestedPath`
- ✅ `e0 check` still works, now reads from `tests/school-checks/` — Task 1 Step 9
- ✅ Dead functions removed — Task 1 Step 10
- ✅ `catalog.json` loses `contentTag`/`requiresE0`, gains `skills` — Task 1 Step 11
- ✅ Submodules removed from template — Task 4 Steps 1–3
- ✅ Tests use local HTTP servers — Task 2
- ✅ All test files updated — Task 3

**Placeholder scan:** None found.

**Type consistency:** `download_checks(root, task_id, config)` is defined in Task 1 Step 5 and called in `cmd_start` in the same step. `school_checks_dir(root, task_id)` defined in Task 1 Step 1, used in Steps 9 and throughout tests. `task_content_dir(root, task_id)` defined Step 1, used in Steps 7 and tests. All consistent.
