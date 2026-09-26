import json

import pytest


@pytest.fixture
def started(run_e0, student_repo, write_task_file, set_issues):
    """T010 fetched, personalized, and marked in progress by an open issue."""
    run_e0(["init"], student_repo)
    write_task_file(student_repo, "T010")
    run_e0(["start", "T010"], student_repo)
    set_issues(student_repo, [("T010", "OPEN")])
    return student_repo


def test_check_fails_before_the_student_writes_any_code(run_e0, started):
    payload, code = run_e0(["check", "T010"], started)
    assert code == 0
    assert "problem" in payload
    assert payload["data"]["passed"] is False


def test_check_passes_once_the_code_is_correct(run_e0, started):
    (started / "greeting.py").write_text(
        'def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8"
    )
    payload, code = run_e0(["check", "T010"], started)

    assert code == 0
    assert "problem" not in payload
    assert payload["data"]["passed"] is True


def test_check_reports_test_output(run_e0, started):
    (started / "greeting.py").write_text(
        'def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8"
    )
    payload, _ = run_e0(["check", "T010"], started)
    assert "test_greet_returns_expected_string" in payload["data"]["output"]


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


def test_check_uses_the_in_progress_task_by_default(run_e0, started):
    """The in-progress task is the one with an open issue."""
    payload, _ = run_e0(["check"], started)
    assert payload["data"]["taskId"] == "T010"


def test_check_without_an_id_and_without_an_open_issue_gives_guidance(run_e0, started, set_issues):
    set_issues(started, [])
    payload, code = run_e0(["check"], started)
    assert code == 0
    assert "problem" in payload
    assert "e0 check <taskId>" in payload["guidance"]


def test_check_with_an_id_does_not_need_gh(run_e0, started, gh_unavailable):
    gh_unavailable(started)
    payload, _ = run_e0(["check", "T010"], started)
    assert "data" in payload
    assert payload["data"]["taskId"] == "T010"


# conversation (2026-09-26): the student runs the tests with one plain command; the run must
# leave a trace that e0 status reads, and the student must be able to see that trace.


def _pytest(repo, *args):
    import subprocess
    import sys

    return subprocess.run(
        [sys.executable, "-m", "pytest", "tests/school-checks/t010", "-v", *args],
        cwd=str(repo), capture_output=True, text=True,
    )


def test_the_students_own_test_run_is_recorded_for_status(run_e0, started, set_issues):
    checks = started / "tests" / "school-checks" / "t010"
    assert (checks / "conftest.py").exists(), "e0 task writes the trace hook with the checks"

    proc = _pytest(started)
    assert proc.returncode != 0
    assert "Exit0: 0 of 1 checks for T010 pass" in proc.stdout, "the student sees the line"
    results = json.loads((checks / "results.json").read_text(encoding="utf-8"))
    assert results["passing"] is False and results["failed"] == 1
    assert results["failedTests"] and "test_greet_returns_expected_string" in results["failedTests"][0]

    payload, _ = run_e0(["status"], started)
    last_run = payload["data"]["inProgress"][0]["checks"]["lastRun"]
    assert last_run["passing"] is False
    assert last_run["failed"] == 1 and last_run["passed"] == 0
    assert last_run["ranAt"]

    (started / "greeting.py").write_text('def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8")
    proc = _pytest(started)
    assert proc.returncode == 0
    assert "Exit0: 1 of 1 checks for T010 pass" in proc.stdout
    payload, _ = run_e0(["status"], started)
    last_run = payload["data"]["inProgress"][0]["checks"]["lastRun"]
    assert last_run == {**last_run, "passing": True, "passed": 1, "failed": 0, "failedTests": []}


def test_e0_check_leaves_the_same_trace(run_e0, started):
    (started / "greeting.py").write_text('def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8")
    run_e0(["check", "T010"], started)
    results = json.loads((started / "tests" / "school-checks" / "t010" / "results.json").read_text(encoding="utf-8"))
    assert results["passing"] is True


def test_the_trace_counts_only_the_tasks_own_tests(run_e0, started):
    """A student who runs `pytest` over the whole repo must not get their own tests counted
    as school checks."""
    import subprocess
    import sys

    (started / "tests" / "test_mine.py").write_text("def test_mine():\n    assert False\n", encoding="utf-8")
    (started / "greeting.py").write_text('def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8")
    subprocess.run([sys.executable, "-m", "pytest", "tests"], cwd=str(started), capture_output=True, text=True)
    results = json.loads((started / "tests" / "school-checks" / "t010" / "results.json").read_text(encoding="utf-8"))
    assert results == {**results, "passing": True, "passed": 1, "failed": 0}


def test_nothing_about_the_tests_is_stored_in_exit0_state(run_e0, started):
    run_e0(["check", "T010"], started)
    state = started / ".exit0" / "state"
    assert [p.name for p in state.iterdir()] == ["profile.json"]


def test_check_on_a_task_that_was_never_fetched_gives_guidance(run_e0, started):
    payload, code = run_e0(["check", "T020"], started)
    assert code == 0
    assert "problem" in payload
    assert "e0 task T020" in payload["guidance"]
