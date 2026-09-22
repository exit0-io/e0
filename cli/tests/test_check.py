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


def test_check_on_a_task_that_was_never_fetched_gives_guidance(run_e0, started):
    payload, code = run_e0(["check", "T020"], started)
    assert code == 0
    assert "problem" in payload
    assert "e0 task T020" in payload["guidance"]
