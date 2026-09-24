import pytest


@pytest.fixture
def initialized(run_e0, student_repo):
    run_e0(["init"], student_repo)
    return student_repo


# ---------------------------------------------------------------- e0 task


def test_task_returns_canonical_text_in_envelope(run_e0, initialized):
    payload, code = run_e0(["task", "T010"], initialized)
    assert code == 0
    assert "problem" not in payload
    canonical = payload["data"]["canonical"]
    assert "<!-- e0:variant" in canonical, "the agent personalizes; e0 hands over the original"
    assert "Build it using the **standard library** only." in canonical


def test_task_does_not_write_the_task_file(run_e0, initialized):
    """Writing the personalized file is the agent's job."""
    run_e0(["task", "T010"], initialized)
    assert not (initialized / "content" / "t010" / "task.md").exists()
    assert not (initialized / ".exit0" / "tasks").exists()


def test_task_downloads_check_files_to_school_checks(run_e0, initialized):
    run_e0(["task", "T010"], initialized)
    checks = initialized / "tests" / "school-checks" / "t010"
    assert (checks / "test_greeting.py").exists()
    assert (checks / "checks.json").exists()


def test_task_emits_variants_with_their_branches(run_e0, initialized):
    payload, _ = run_e0(["task", "T010"], initialized)
    variants = payload["data"]["personalization"]["variants"]
    assert len(variants) == 1
    assert variants[0]["id"] == "run-tests"
    assert {tuple(sorted(b["when"].items())) for b in variants[0]["branches"]} == {
        (("os", "linux"),),
        (("os", "macos"),),
        (("os", "windows"),),
    }


def test_task_emits_retone_blocks(run_e0, initialized):
    payload, _ = run_e0(["task", "T010"], initialized)
    blocks = payload["data"]["personalization"]["retoneBlocks"]
    assert len(blocks) == 1
    assert blocks[0]["basedOn"] == "the student's Python experience"


def test_task_emits_only_facts_referenced_by_variants(run_e0, initialized):
    payload, _ = run_e0(["task", "T010"], initialized)
    facts = payload["data"]["personalization"]["facts"]
    assert set(facts) == {"os"}


def test_task_reports_the_path_the_agent_must_write(run_e0, initialized):
    payload, _ = run_e0(["task", "T010"], initialized)
    assert payload["data"]["paths"]["task"] == "content/t010/task.md"
    assert payload["data"]["paths"]["checks"] == "tests/school-checks/t010"


def test_task_does_not_start_anything(run_e0, initialized):
    """'Tell me more about T010' must not change the student's progress."""
    payload, _ = run_e0(["task", "T010"], initialized)
    assert payload["data"]["status"] == "not_started"
    assert "issue" not in payload["data"]
    status, _ = run_e0(["status"], initialized)
    assert status["data"]["inProgress"] == []


def test_task_passes_the_whole_catalog_entry_through(run_e0, initialized):
    """Whatever the course author adds to the catalog reaches the agent unchanged."""
    payload, _ = run_e0(["task", "T010"], initialized)
    task = payload["data"]["task"]
    assert task["title"] == "Say hello"
    assert task["relatedTopics"] == ["intro-to-linux"]
    assert task["purpose"]


def test_task_reports_status_and_unmet_dependencies_from_issues(run_e0, initialized, set_issues):
    payload, _ = run_e0(["task", "T020"], initialized)
    assert payload["data"]["unmetDependencies"] == ["T010"]

    set_issues(initialized, [("T010", "CLOSED"), ("T020", "OPEN")])
    payload, _ = run_e0(["task", "T020"], initialized)
    assert payload["data"]["status"] == "in_progress"
    assert payload["data"]["unmetDependencies"] == []


def test_task_still_works_when_gh_is_not_set_up(run_e0, initialized, gh_unavailable):
    """Talking about a task must not depend on GitHub. Progress becomes a warning."""
    gh_unavailable(initialized)
    payload, _ = run_e0(["task", "T010"], initialized)
    assert "problem" not in payload
    assert payload["data"]["canonical"]
    assert payload["data"]["status"] == "unknown"
    assert any(w["kind"] == "progress" for w in payload["data"]["warnings"])


def test_task_does_not_include_rules_in_envelope(run_e0, initialized):
    payload, _ = run_e0(["task", "T010"], initialized)
    assert "rules" not in payload["data"]


def test_task_accepts_a_lowercase_task_id(run_e0, initialized):
    payload, _ = run_e0(["task", "t010"], initialized)
    assert "problem" not in payload
    assert payload["data"]["taskId"] == "T010"


def test_task_with_an_unknown_id_lists_valid_ids(run_e0, initialized):
    payload, code = run_e0(["task", "T999"], initialized)
    assert code == 0
    assert "problem" in payload
    assert "T010" in payload["guidance"]


def test_task_without_an_id_is_a_problem(run_e0, initialized):
    payload, _ = run_e0(["task"], initialized)
    assert "problem" in payload


# ---------------------------------------------------------------- e0 start


def test_start_emits_an_issue_whose_body_is_the_whole_personalized_task(
    run_e0, initialized, write_task_file
):
    text = write_task_file(initialized, "T010")
    payload, code = run_e0(["start", "T010"], initialized)
    assert code == 0
    assert "problem" not in payload
    issue = payload["data"]["issue"]
    assert issue["title"] == "[T010] Say hello"
    assert issue["body"] == text
    assert "<!--" not in issue["body"]
    assert "standard library" in issue["body"]


def test_start_on_the_first_task_points_at_the_branch_walk(
    run_e0, initialized, write_task_file, set_issues
):
    """conversation (2026-09-24): after the first issue the agent sent the start template's three
    branch commands, not git.md's step-by-step walk. It never read git.md: the only signal was a
    line after the literal template. e0 says it is the first task and where the walk lives."""
    write_task_file(initialized, "T010")
    payload, _ = run_e0(["start", "T010"], initialized)
    assert payload["data"]["firstTask"] is True
    assert ".exit0/skills/learning/references/git.md" in payload["message"]
    assert "The branch, step by step" in payload["message"]
    assert "git checkout main" in payload["message"]

    write_task_file(initialized, "T020")
    set_issues(initialized, [("T010", "CLOSED")])
    payload, _ = run_e0(["start", "T020"], initialized)
    assert payload["data"]["firstTask"] is False
    assert "git.md" not in payload["message"]


def test_start_stores_nothing_locally(run_e0, initialized, write_task_file):
    """The open issue is the record. e0 keeps no progress of its own."""
    write_task_file(initialized, "T010")
    run_e0(["start", "T010"], initialized)
    state = initialized / ".exit0" / "state"
    assert [p.name for p in state.iterdir()] == ["profile.json"]
    assert not (initialized / ".exit0" / "tasks").exists()


def test_start_before_the_task_file_exists_points_at_e0_task(run_e0, initialized):
    payload, code = run_e0(["start", "T010"], initialized)
    assert code == 0
    assert "problem" in payload
    assert "e0 task T010" in payload["guidance"]
    assert "issue" not in payload


def test_start_verifies_the_task_file_first(run_e0, initialized, write_task_file):
    text = write_task_file(initialized, "T010")
    task_file = initialized / "content" / "t010" / "task.md"
    task_file.write_text(
        text.replace("**standard library**", "**requests library**"), encoding="utf-8"
    )
    payload, _ = run_e0(["start", "T010"], initialized)
    assert "problem" in payload
    assert payload["data"]["violations"]
    assert "issue" not in payload


def test_start_refuses_a_task_that_already_has_an_issue(run_e0, initialized, write_task_file, set_issues):
    write_task_file(initialized, "T010")
    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["start", "T010"], initialized)
    assert "problem" in payload
    assert "in progress" in payload["problem"]
    assert "#1" in payload["problem"]

    set_issues(initialized, [("T010", "CLOSED")])
    payload, _ = run_e0(["start", "T010"], initialized)
    assert "problem" in payload
    assert "complete" in payload["problem"]


def test_start_warns_about_unmet_dependencies_but_proceeds(run_e0, initialized, write_task_file):
    write_task_file(initialized, "T020")
    payload, code = run_e0(["start", "T020"], initialized)
    assert code == 0
    assert "problem" not in payload
    assert any(warning["kind"] == "dependency" for warning in payload["data"]["warnings"])
    assert payload["data"]["issue"]["title"] == "[T020] Say goodbye"


def test_start_needs_gh(run_e0, initialized, write_task_file, gh_unavailable):
    """Without the issues e0 cannot know whether the task already started."""
    write_task_file(initialized, "T010")
    gh_unavailable(initialized)
    payload, _ = run_e0(["start", "T010"], initialized)
    assert "problem" in payload
    assert "gh auth" in payload["guidance"]


def test_start_with_an_unknown_task_lists_valid_ids(run_e0, initialized):
    payload, code = run_e0(["start", "T999"], initialized)
    assert code == 0
    assert "problem" in payload
    assert "T010" in payload["guidance"]


def test_start_without_a_task_id_is_a_problem(run_e0, initialized):
    payload, code = run_e0(["start"], initialized)
    assert code == 0
    assert "problem" in payload


def test_profile_get_on_fresh_repo_detects_os(run_e0, student_repo):
    payload, code = run_e0(["profile", "get"], student_repo)
    assert code == 0
    assert "problem" not in payload
    assert "os" in payload["data"]["profile"]
