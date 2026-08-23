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
