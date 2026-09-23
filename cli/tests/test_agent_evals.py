"""Agent evals: run the real coding agent against a fixture course repo and check what it
says and does.

Each scenario in evals/*.json is a conversation the maintainer reviewed (a conversation*.md
with {comments}), boiled down to: the state of the student's repo, what the student says,
and what the agent must and must not do in reply. The unit tests pin e0. These pin the
skill, as a cheap model actually follows it.

They call `claude -p` with the cheapest model, so they cost money and take minutes.
Run them on purpose:

    E0_AGENT_EVALS=1 ../.venv/bin/python -m pytest tests/test_agent_evals.py -v

Scenarios with "bootstrap": true download e0 from GitHub. They also need
E0_AGENT_EVALS_NETWORK=1, because they only pass once the pinned release is published.
Scenarios with "pinned_release_missing": true bootstrap offline: a fake curl answers 404
for the pinned release and serves the local e0 as the latest release.
Scenarios with "downloads_fail": true get a fake curl that answers 404 for every download.
"""

import json
import os
import pathlib
import re
import shutil
import subprocess

import pytest

from conftest import ISSUES_FILE, PRS_FILE, E0_PATH, ROOT_TEMPLATE, _git

EVALS = pathlib.Path(__file__).resolve().parent / "evals"
SCENARIOS = sorted(EVALS.glob("*.json"))

pytestmark = pytest.mark.skipif(
    os.environ.get("E0_AGENT_EVALS") != "1",
    reason="agent evals run the real coding agent; set E0_AGENT_EVALS=1",
)


FAKE_CURL = f"""#!/usr/bin/env python3
import shutil, sys
SERVE_LATEST = {{serve_latest}}
args = sys.argv[1:]
url = next((a for a in args if a.startswith("http")), "")
out = args[args.index("-o") + 1] if "-o" in args else None
if SERVE_LATEST and "/releases/latest/download/e0" in url and out:
    shutil.copy({str(E0_PATH)!r}, out)
    sys.exit(0)
print("curl: (22) The requested URL returned error: 404", file=sys.stderr)
sys.exit(22)
"""


def _scenario_id(path):
    return path.stem


@pytest.fixture
def agent_repo(tmp_path, content_server, framework_server, fake_gh_bin):
    """A student's fork right after cloning: the template files, config pointed at the local
    servers, a fake gh on PATH. e0 is installed unless the scenario bootstraps it."""

    def _make(scenario):
        repo = tmp_path / "student-repo"
        shutil.copytree(ROOT_TEMPLATE, repo, symlinks=True)
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
        with (repo / ".gitignore").open("a", encoding="utf-8") as handle:
            handle.write(f"\n{ISSUES_FILE}\n{PRS_FILE}\n")
        _git(repo, "init", "-q", "-b", "main")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "initial")
        if scenario.get("branch"):
            _git(repo, "checkout", "-q", "-b", scenario["branch"])

        if scenario.get("pinned_release_missing") or scenario.get("downloads_fail"):
            curl = fake_gh_bin / "curl"
            serve_latest = not scenario.get("downloads_fail")
            curl.write_text(FAKE_CURL.format(serve_latest=serve_latest), encoding="utf-8")
            curl.chmod(0o755)
        elif not scenario.get("bootstrap"):
            shutil.copy(E0_PATH, repo / ".exit0" / "e0")
            (repo / ".exit0" / "e0").chmod(0o755)
            subprocess.run([str(repo / ".exit0" / "e0"), "init"], cwd=repo, check=True, capture_output=True)

        issues = [
            {
                "number": n,
                "title": f"[{task}] title",
                "state": state,
                "url": f"https://github.com/student/repo/issues/{n}",
            }
            for n, (task, state) in enumerate(scenario.get("issues", []), start=1)
        ]
        prs = [
            {
                "number": 100 + n,
                "title": f"[{task}] solution",
                "state": state,
                "url": f"https://github.com/student/repo/pull/{100 + n}",
                "body": "",
            }
            for n, (task, state) in enumerate(scenario.get("prs", []), start=1)
        ]
        (repo / ISSUES_FILE).write_text(json.dumps(issues), encoding="utf-8")
        (repo / PRS_FILE).write_text(json.dumps(prs), encoding="utf-8")
        return repo

    return _make


class Turn:
    def __init__(self, session_id, texts, commands, raw):
        self.session_id = session_id
        self.text = "\n".join(texts)
        self.commands = commands
        self.raw = raw


def run_agent(repo, message, fake_gh_bin, session_id=None, timeout=420):
    """One student turn. Returns the agent's text and the shell commands it ran."""
    env = dict(os.environ)
    env["PATH"] = f"{fake_gh_bin}{os.pathsep}{env.get('PATH', '')}"
    command = [
        "claude", "-p", message,
        "--model", os.environ.get("E0_AGENT_EVALS_MODEL", "haiku"),
        "--output-format", "stream-json", "--verbose",
        "--permission-mode", "acceptEdits",
        "--allowedTools", "Bash", "Read", "Write", "Edit", "Glob", "Grep", "TodoWrite",
        "--max-turns", "40",
    ]
    if session_id:
        command += ["--resume", session_id]
    proc = subprocess.run(command, cwd=str(repo), capture_output=True, text=True, env=env, timeout=timeout)

    texts, commands, sid = [], [], session_id
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            sid = event.get("session_id", sid)
        if event.get("type") == "assistant":
            for block in event["message"].get("content", []):
                if block.get("type") == "text":
                    texts.append(block["text"])
                elif block.get("type") == "tool_use" and block.get("name") == "Bash":
                    commands.append(block["input"].get("command", ""))
    assert proc.returncode == 0 or texts, f"claude failed: {proc.stderr[-2000:]}"
    return Turn(sid, texts, commands, proc.stdout)


def _check(turn, expectations, label):
    joined_commands = "\n".join(turn.commands)
    failures = []
    for pattern in expectations.get("must_match", []):
        if not re.search(pattern, turn.text, re.IGNORECASE | re.DOTALL):
            failures.append(f"reply should match /{pattern}/")
    for pattern in expectations.get("must_not_match", []):
        if re.search(pattern, turn.text, re.IGNORECASE | re.DOTALL):
            failures.append(f"reply must not match /{pattern}/")
    for pattern in expectations.get("must_run", []):
        if not re.search(pattern, joined_commands):
            failures.append(f"agent should have run /{pattern}/")
    for pattern in expectations.get("must_not_run", []):
        if re.search(pattern, joined_commands):
            failures.append(f"agent must not run /{pattern}/")
    assert not failures, (
        f"{label}:\n  - " + "\n  - ".join(failures)
        + f"\n\n--- reply ---\n{turn.text}\n\n--- commands ---\n{joined_commands}"
    )


@pytest.mark.parametrize("path", SCENARIOS, ids=_scenario_id)
def test_agent_follows_the_learning_skill(path, agent_repo, fake_gh_bin):
    scenario = json.loads(path.read_text(encoding="utf-8"))
    if scenario.get("bootstrap") and os.environ.get("E0_AGENT_EVALS_NETWORK") != "1":
        pytest.skip("bootstrap scenarios download e0 from GitHub; set E0_AGENT_EVALS_NETWORK=1")

    repo = agent_repo(scenario)
    session_id = None
    for index, step in enumerate(scenario["turns"], start=1):
        turn = run_agent(repo, step["say"], fake_gh_bin, session_id=session_id)
        session_id = turn.session_id
        _check(turn, step, f"{path.stem}, turn {index} ({step['say']!r})")
