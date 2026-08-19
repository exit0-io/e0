import json


def test_repo_root_finds_the_git_root_from_a_subdirectory(e0mod, student_repo):
    nested = student_repo / "src" / "deep"
    nested.mkdir(parents=True)
    assert e0mod.repo_root(nested) == student_repo


def test_repo_root_returns_none_outside_a_repo(e0mod, tmp_path):
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    assert e0mod.repo_root(outside) is None


def test_run_git_never_raises_on_a_bad_command(e0mod, student_repo):
    code, out, err = e0mod.run_git(student_repo, "definitely-not-a-git-command")
    assert code != 0
    assert isinstance(out, str) and isinstance(err, str)


def test_append_and_read_events_roundtrip(e0mod, student_repo):
    e0mod.append_event(student_repo, "task_started", taskId="T010")
    e0mod.append_event(student_repo, "task_completed", taskId="T010")
    events = e0mod.read_events(student_repo)

    assert [event["event"] for event in events] == ["task_started", "task_completed"]
    assert events[0]["taskId"] == "T010"
    assert "ts" in events[0]


def test_read_events_skips_malformed_lines(e0mod, student_repo):
    e0mod.append_event(student_repo, "task_started", taskId="T010")
    log = e0mod.exit0_dir(student_repo) / "state" / "events.jsonl"
    with log.open("a", encoding="utf-8") as handle:
        handle.write("this is not json\n")
    e0mod.append_event(student_repo, "task_completed", taskId="T010")

    events = e0mod.read_events(student_repo)
    assert [event["event"] for event in events] == ["task_started", "task_completed"]


def test_read_events_on_a_fresh_repo_is_empty(e0mod, student_repo):
    assert e0mod.read_events(student_repo) == []


def test_detect_profile_reports_only_the_os(e0mod, student_repo):
    """os is the only fact e0 can reliably observe on its own."""
    profile = e0mod.detect_profile(student_repo)
    assert profile == {"os": profile["os"]}
    assert profile["os"] in {"linux", "macos", "windows"}


def test_shell_and_test_framework_are_set_by_the_student_not_detected(run_e0, student_repo):
    """These facts come from an onboarding task via profile set, never from detection."""
    payload, code = run_e0(["profile", "set", "shell", "bash"], student_repo)
    assert code == 0 and payload["ok"] is True
    assert payload["data"]["profile"]["shell"] == "bash"

    payload, _ = run_e0(["profile", "set", "testFramework", "pytest"], student_repo)
    assert payload["data"]["profile"]["testFramework"] == "pytest"


def test_profile_get_and_set_via_the_command(run_e0, student_repo):
    payload, code = run_e0(["profile", "set", "testFramework", "unittest"], student_repo)
    assert code == 0 and payload["ok"] is True

    payload, _ = run_e0(["profile", "get"], student_repo)
    assert payload["data"]["profile"]["testFramework"] == "unittest"


def test_profile_set_without_a_value_is_a_problem(run_e0, student_repo):
    payload, code = run_e0(["profile", "set", "testFramework"], student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "value" in payload["guidance"].lower()


def test_commands_outside_a_git_repo_give_guidance(run_e0, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    payload, code = run_e0(["profile", "get"], outside)
    assert code == 0
    assert payload["ok"] is False
    assert "course" in payload["guidance"].lower()
