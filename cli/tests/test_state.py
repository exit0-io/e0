import os


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


def test_run_gh_never_raises_when_gh_is_missing(e0mod, student_repo, monkeypatch):
    monkeypatch.setenv("PATH", "")
    code, out, err = e0mod.run_gh(student_repo, "issue", "list")
    assert code != 0
    assert isinstance(err, str)


def test_e0_has_no_event_log(e0mod):
    """Progress lives in GitHub issues. e0 must not keep a shadow copy in the repo."""
    assert not hasattr(e0mod, "append_event")
    assert not hasattr(e0mod, "read_events")


def test_github_progress_maps_issue_titles_to_tasks(
    e0mod, run_e0, student_repo, set_issues, fake_gh_bin, monkeypatch
):
    run_e0(["init"], student_repo)
    catalog = e0mod.read_catalog(student_repo)
    set_issues(student_repo, [("T010", "CLOSED"), ("T020", "OPEN")])
    monkeypatch.setenv("PATH", f"{fake_gh_bin}{os.pathsep}{os.environ['PATH']}")

    progress, error = e0mod.github_progress(student_repo, catalog)
    assert error is None
    assert e0mod.statuses_from(progress) == {"T010": "complete", "T020": "in_progress"}
    assert progress["T020"]["issue"]["number"] == 2


def test_github_progress_reports_a_gh_failure_as_text(
    e0mod, run_e0, student_repo, gh_unavailable, fake_gh_bin, monkeypatch
):
    run_e0(["init"], student_repo)
    catalog = e0mod.read_catalog(student_repo)
    gh_unavailable(student_repo)
    monkeypatch.setenv("PATH", f"{fake_gh_bin}{os.pathsep}{os.environ['PATH']}")

    progress, error = e0mod.github_progress(student_repo, catalog)
    assert progress is None
    assert "gh auth login" in error


def test_detect_profile_reports_only_the_os(e0mod, student_repo):
    """os is the only fact e0 can reliably observe on its own."""
    profile = e0mod.detect_profile(student_repo)
    assert profile == {"os": profile["os"]}
    assert profile["os"] in {"linux", "macos", "windows"}


def test_shell_and_test_framework_are_set_by_the_student_not_detected(run_e0, student_repo):
    """These facts come from an onboarding task via profile set, never from detection."""
    payload, code = run_e0(["profile", "set", "shell", "bash"], student_repo)
    assert code == 0 and "problem" not in payload
    assert payload["data"]["profile"]["shell"] == "bash"

    payload, _ = run_e0(["profile", "set", "testFramework", "pytest"], student_repo)
    assert payload["data"]["profile"]["testFramework"] == "pytest"


def test_profile_get_and_set_via_the_command(run_e0, student_repo):
    payload, code = run_e0(["profile", "set", "testFramework", "unittest"], student_repo)
    assert code == 0 and "problem" not in payload

    payload, _ = run_e0(["profile", "get"], student_repo)
    assert payload["data"]["profile"]["testFramework"] == "unittest"


def test_profile_set_without_a_value_is_a_problem(run_e0, student_repo):
    payload, code = run_e0(["profile", "set", "testFramework"], student_repo)
    assert code == 0
    assert "problem" in payload
    assert "value" in payload["guidance"].lower()


def test_commands_outside_a_git_repo_give_guidance(run_e0, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    payload, code = run_e0(["profile", "get"], outside)
    assert code == 0
    assert "problem" in payload
    assert "course" in payload["guidance"].lower()
