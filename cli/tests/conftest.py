import importlib.machinery
import importlib.util
import json
import os
import pathlib
import subprocess
import sys

import pytest

FIXTURE_COURSE = pathlib.Path(__file__).resolve().parent.parent.parent / "courses" / "demo" / "content"
FRAMEWORK_DIR = pathlib.Path(__file__).resolve().parents[1]

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
