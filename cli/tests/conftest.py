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


_COVERAGE_CFG = str(pathlib.Path(__file__).resolve().parents[1] / "setup.cfg")


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
            # allow local file:// transport so submodule add works in tests
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "protocol.file.allow",
            "GIT_CONFIG_VALUE_0": "always",
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
