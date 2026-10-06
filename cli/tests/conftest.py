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
ROOT_TEMPLATE = pathlib.Path(__file__).resolve().parents[2] / "courses" / "demo" / "template"


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


ISSUES_FILE = ".fake-gh-issues.json"
PRS_FILE = ".fake-gh-prs.json"
DIFF_FILE = ".fake-gh-diff.txt"

DEFAULT_DIFF = """diff --git a/greeting.py b/greeting.py
new file mode 100644
--- /dev/null
+++ b/greeting.py
@@ -0,0 +1,2 @@
+def greet(name):
+    return f"Hello, {name}!"
"""

# A stand-in for the GitHub CLI, good enough for e0 and for the agent evals.
#   gh issue list / gh pr list  -> print the records in <repo>/.fake-gh-issues.json or
#                                  .fake-gh-prs.json (an empty list if the file is missing)
#   gh issue create             -> append an OPEN issue and print its URL, like the real one
#   gh issue comment N          -> append a comment to issue N and print its URL
#   gh pr diff N                -> print <repo>/.fake-gh-diff.txt, or a small default diff
#   gh pr review N --comment    -> append a review to PR N
#   gh auth status              -> succeed
# A .fake-gh-issues.json holding {"error": "..."} makes every command fail the way a
# logged-out gh would. The files live at the git root, so cwd inside the repo is fine.
FAKE_GH = f"""#!/usr/bin/env python3
import json, os, subprocess, sys

def root():
    try:
        return subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return os.getcwd()

def load(name):
    path = os.path.join(root(), name)
    if not os.path.exists(path):
        return []
    return json.load(open(path, encoding="utf-8"))

def save(name, data):
    json.dump(data, open(os.path.join(root(), name), "w", encoding="utf-8"))

def body_from(args):
    for i, a in enumerate(args):
        if a in ("--body", "-b"): return args[i + 1]
        if a in ("--body-file", "-F"): return open(args[i + 1], encoding="utf-8").read()
    return ""

def find(records, number):
    for record in records:
        if str(record.get("number")) == str(number):
            return record
    print("fake gh: no record #" + str(number), file=sys.stderr)
    sys.exit(1)

issues = load({ISSUES_FILE!r})
if isinstance(issues, dict) and "error" in issues:
    print(issues["error"], file=sys.stderr)
    sys.exit(4)

args = sys.argv[1:]
if args[:2] == ["issue", "list"]:
    print(json.dumps(issues))
elif args[:2] == ["pr", "list"]:
    print(json.dumps(load({PRS_FILE!r})))
elif args[:2] == ["issue", "create"]:
    title = ""
    for i, a in enumerate(args):
        if a in ("--title", "-t"): title = args[i + 1]
    number = max([i.get("number", 0) for i in issues] + [0]) + 1
    url = f"https://github.com/student/repo/issues/{{number}}"
    issues.append({{"number": number, "title": title, "state": "OPEN", "url": url, "body": body_from(args)}})
    save({ISSUES_FILE!r}, issues)
    print(url)
elif args[:2] == ["issue", "comment"]:
    issue = find(issues, args[2])
    comments = issue.setdefault("comments", [])
    comments.append({{"body": body_from(args), "author": {{"login": "student"}}}})
    save({ISSUES_FILE!r}, issues)
    print(issue["url"] + "#issuecomment-" + str(len(comments)))
elif args[:2] == ["pr", "diff"]:
    path = os.path.join(root(), {DIFF_FILE!r})
    print(open(path, encoding="utf-8").read() if os.path.exists(path) else {DEFAULT_DIFF!r})
elif args[:2] == ["pr", "review"]:
    prs = load({PRS_FILE!r})
    pr = find(prs, args[2])
    pr.setdefault("reviews", []).append(
        {{"body": body_from(args), "state": "COMMENTED", "author": {{"login": "student"}}}})
    save({PRS_FILE!r}, prs)
elif args[:2] == ["auth", "status"]:
    print("Logged in to github.com as student")
else:
    print("fake gh: unsupported command: " + " ".join(args), file=sys.stderr)
    sys.exit(1)
"""


@pytest.fixture
def fake_gh_bin(tmp_path):
    directory = tmp_path / "fake-bin"
    directory.mkdir()
    script = directory / "gh"
    script.write_text(FAKE_GH, encoding="utf-8")
    script.chmod(0o755)
    return directory


@pytest.fixture
def set_issues():
    """Write the GitHub issues the fake gh should report for a repo.

    set_issues(repo, [("T010", "OPEN"), ("T020", "CLOSED")]) or a raw list of issue dicts.
    """

    def _set(repo, issues):
        records = []
        for index, item in enumerate(issues, start=1):
            if isinstance(item, tuple):
                task_id, state = item
                item = {
                    "number": index,
                    "title": f"[{task_id}] some title",
                    "state": state,
                    "url": f"https://github.com/student/repo/issues/{index}",
                }
            records.append(item)
        (pathlib.Path(repo) / ISSUES_FILE).write_text(json.dumps(records), encoding="utf-8")

    return _set


@pytest.fixture
def set_prs():
    """Write the pull requests the fake gh should report.

    set_prs(repo, [("T010", "MERGED")]) links by title; a dict lets you link by body ("#1").
    """

    def _set(repo, prs):
        records = []
        for index, item in enumerate(prs, start=101):
            if isinstance(item, tuple):
                task_id, state, *extra = item
                item = {
                    "number": index,
                    "title": f"[{task_id}] my solution",
                    "state": state,
                    "url": f"https://github.com/student/repo/pull/{index}",
                    "body": "",
                    "headRefName": f"{task_id.lower()}-my-solution",
                    **(extra[0] if extra else {}),
                }
            records.append(item)
        (pathlib.Path(repo) / PRS_FILE).write_text(json.dumps(records), encoding="utf-8")

    return _set


# Shapes gh gives statusCheckRollup in, for tests and evals: a CheckRun and a StatusContext.
CI_PASSING = [{"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SUCCESS"}]
CI_FAILING = [
    {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SUCCESS"},
    {"__typename": "StatusContext", "state": "FAILURE"},
]
CI_PENDING = [{"__typename": "CheckRun", "status": "IN_PROGRESS", "conclusion": None}]


@pytest.fixture
def gh_unavailable():
    def _break(repo, error="gh: To get started with GitHub CLI, please run: gh auth login"):
        (pathlib.Path(repo) / ISSUES_FILE).write_text(json.dumps({"error": error}), encoding="utf-8")

    return _break


@pytest.fixture
def run_e0(fake_gh_bin):
    """Invoke e0 as a real subprocess and return (parsed_json, exit_code)."""

    def _run(args, cwd, env=None):
        merged = dict(os.environ)
        merged.update(env or {})
        merged["PATH"] = f"{fake_gh_bin}{os.pathsep}{merged.get('PATH', '')}"
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
        "tests/school-checks/\n"
        f"{ISSUES_FILE}\n"
        f"{PRS_FILE}\n",
        encoding="utf-8",
    )
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "initial")
    return repo


@pytest.fixture
def personalize(e0mod):
    """What the agent does with `e0 task` output: keep the matching variant branch, leave
    retone blocks as given (or fill them with `note`), strip every marker."""

    def _personalize(task_payload, note=None):
        canonical = task_payload["data"]["canonical"]
        facts = task_payload["data"]["personalization"]["facts"]
        parts = []
        for region in e0mod.parse_regions(canonical):
            if region["kind"] == "fixed":
                parts.append(region["text"])
            elif region["kind"] == "variant":
                chosen = e0mod.select_branch(region["branches"], facts) or region["branches"][0]
                parts.append(chosen["text"] + "\n")
            elif note is not None:
                parts.append(note + "\n")
            else:
                parts.append(region["text"])
        return "".join(parts)

    return _personalize


@pytest.fixture
def write_task_file(run_e0, personalize):
    """Run `e0 task <id>` and write the personalized file, as the agent would. Returns the text."""

    def _write(repo, task_id, note=None):
        payload, _ = run_e0(["task", task_id], repo)
        assert "problem" not in payload, payload
        text = personalize(payload, note=note)
        path = pathlib.Path(repo) / payload["data"]["paths"]["task"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return text

    return _write
