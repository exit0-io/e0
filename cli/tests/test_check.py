import pytest


@pytest.fixture
def started(run_e0, student_repo):
    run_e0(["init"], student_repo)
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
