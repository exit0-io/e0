import json

import pytest

from conftest import _git


@pytest.fixture
def initialized(run_e0, student_repo):
    run_e0(["init"], student_repo)
    return student_repo


@pytest.fixture
def git():
    return _git


def test_status_on_a_fresh_course_lists_the_ready_tasks(run_e0, initialized):
    payload, code = run_e0(["status"], initialized)
    assert code == 0
    assert "problem" not in payload
    assert [task["id"] for task in payload["data"]["next"]] == ["T010"]
    assert payload["data"]["inProgress"] == []
    assert payload["data"]["completed"] == []


def test_progress_comes_from_github_issues(run_e0, initialized, set_issues):
    """An open issue titled [T010] ... is in progress. A closed one is complete."""
    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert [task["id"] for task in payload["data"]["inProgress"]] == ["T010"]
    assert payload["data"]["inProgress"][0]["issue"]["number"] == 1
    assert payload["data"]["next"] == []
    assert "T010" in payload["message"]

    set_issues(initialized, [("T010", "CLOSED")])
    payload, _ = run_e0(["status"], initialized)
    assert [t["id"] for t in payload["data"]["completed"]] == ["T010"]
    assert [task["id"] for task in payload["data"]["next"]] == ["T020"]


def test_status_next_is_a_list_because_tasks_form_a_tree(run_e0, initialized):
    payload, _ = run_e0(["status"], initialized)
    assert isinstance(payload["data"]["next"], list)
    assert "T020" not in [task["id"] for task in payload["data"]["next"]]


def test_an_open_issue_wins_over_a_closed_one_for_the_same_task(run_e0, initialized, set_issues):
    set_issues(initialized, [("T010", "CLOSED"), ("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert [task["id"] for task in payload["data"]["inProgress"]] == ["T010"]
    assert payload["data"]["completed"] == []


def test_issues_that_are_not_tasks_are_ignored(run_e0, initialized, set_issues):
    set_issues(
        initialized,
        [
            {"number": 7, "title": "Fix the README", "state": "OPEN", "url": "u"},
            {"number": 8, "title": "[T999] not a task", "state": "OPEN", "url": "u"},
            {"number": 9, "title": "[t010] lowercase is fine", "state": "OPEN", "url": "u"},
        ],
    )
    payload, _ = run_e0(["status"], initialized)
    assert [task["id"] for task in payload["data"]["inProgress"]] == ["T010"]


def test_status_message_links_the_issue_of_a_task_in_progress(run_e0, initialized, set_issues):
    """The agent copies the message; the student must be able to click through."""
    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert "https://github.com/student/repo/issues/1" in payload["message"]


def test_status_links_pull_requests_to_tasks(run_e0, initialized, set_issues, set_prs):
    set_issues(initialized, [("T010", "OPEN")])
    set_prs(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    pr = payload["data"]["inProgress"][0]["pr"]
    assert pr["number"] == 101
    assert pr["state"] == "OPEN"
    assert pr["merged"] is False


def test_a_pr_can_be_linked_by_mentioning_the_issue_number(run_e0, initialized, set_issues, set_prs):
    set_issues(initialized, [("T010", "CLOSED")])
    set_prs(
        initialized,
        [{"number": 5, "title": "greeting function", "state": "MERGED", "url": "u", "body": "Closes #1"}],
    )
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["completed"][0]["pr"]["merged"] is True
    assert payload["data"]["warnings"] == []


def test_a_closed_issue_without_a_merged_pr_is_flagged(run_e0, initialized, set_issues, set_prs):
    """The student may skip the PR. The agent must be told, so it can tell them."""
    set_issues(initialized, [("T010", "CLOSED")])
    payload, _ = run_e0(["status"], initialized)
    kinds = {(w["kind"], w["taskId"]) for w in payload["data"]["warnings"]}
    assert kinds == {("closed_without_pr", "T010")}
    assert "reopen" in payload["data"]["warnings"][0]["message"]

    set_prs(initialized, [("T010", "CLOSED")])  # closed, not merged: still flagged
    payload, _ = run_e0(["status"], initialized)
    assert len(payload["data"]["warnings"]) == 1

    set_prs(initialized, [("T010", "CLOSED"), ("T010", "MERGED")])
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["warnings"] == []
    assert payload["data"]["completed"][0]["pr"]["merged"] is True


def test_status_without_gh_is_a_problem_with_guidance(run_e0, initialized, gh_unavailable):
    gh_unavailable(initialized)
    payload, code = run_e0(["status"], initialized)
    assert code == 0
    assert "problem" in payload
    assert "gh auth" in payload["guidance"]


def test_status_carries_no_workflow_text(run_e0, initialized):
    """Procedure lives in the learning skill, not in the status envelope."""
    payload, _ = run_e0(["status"], initialized)
    assert "workflow" not in payload["data"]
    assert "contentTag" not in payload["data"]


def test_nothing_about_progress_is_stored_locally(run_e0, initialized, set_issues):
    set_issues(initialized, [("T010", "OPEN")])
    run_e0(["status"], initialized)
    state = initialized / ".exit0" / "state"
    assert [p.name for p in state.iterdir()] == ["profile.json"]


def test_available_tasks_needs_every_dependency_complete(e0mod, initialized):
    catalog = e0mod.read_catalog(initialized)
    assert [t["id"] for t in e0mod.available_tasks(catalog, {})] == ["T010"]
    assert [t["id"] for t in e0mod.available_tasks(catalog, {"T010": "in_progress"})] == []
    assert [t["id"] for t in e0mod.available_tasks(catalog, {"T010": "complete"})] == ["T020"]


def test_unmet_dependencies_lists_incomplete_prerequisites(e0mod, initialized):
    catalog = e0mod.read_catalog(initialized)
    task = e0mod.find_task(catalog, "T020")
    assert e0mod.unmet_dependencies(task, {}) == ["T010"]
    assert e0mod.unmet_dependencies(task, {"T010": "complete"}) == []


def test_status_always_reports_update_as_unknown(run_e0, initialized):
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["update"] == "unknown"


def test_bare_e0_runs_status(run_e0, initialized):
    payload, code = run_e0([], initialized)
    assert code == 0
    assert payload["command"] == "status"


def test_status_before_init_gives_guidance(run_e0, student_repo):
    payload, code = run_e0(["status"], student_repo)
    assert code == 0
    assert "problem" in payload
    assert "init" in payload["guidance"]


def test_status_reports_the_current_branch(run_e0, initialized, git):
    """conversation.md: the agent must know which branch the student is on, to catch work on
    main and misnamed branches. The fact comes from e0, never inferred."""
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["branch"] == "main"

    git(initialized, "checkout", "-q", "-b", "<task-branch>")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["branch"] == "<task-branch>"


def test_a_task_in_progress_on_main_is_flagged(run_e0, initialized, set_issues, git):
    """conversation.md: task work belongs on a task branch. Nothing in progress: no warning."""
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["warnings"] == []

    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    kinds = {(w["kind"], w["taskId"]) for w in payload["data"]["warnings"]}
    assert kinds == {("on_main", "T010")}
    # evals 07 and 12: a cheap model pasted all three branch commands at once. The warning
    # carries the first command and the pace, so there is nothing to infer.
    message = payload["data"]["warnings"][0]["message"]
    assert "git checkout main" in message
    assert "one command per message" in message
    assert ".exit0/skills/learning/references/git.md" in message

    git(initialized, "checkout", "-q", "-b", "t010-say-hello")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["warnings"] == []


def test_status_never_says_unlock(run_e0, initialized, set_issues):
    """conversation.md: tasks build on each other. This is the industry, not a game."""
    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert "unlock" not in json.dumps(payload).lower()


def test_status_when_all_tasks_complete(run_e0, initialized, set_issues):
    set_issues(initialized, [("T010", "CLOSED"), ("T020", "CLOSED")])
    payload, _ = run_e0(["status"], initialized)
    assert "problem" not in payload
    assert payload["data"]["inProgress"] == []
    assert payload["data"]["next"] == []
    assert payload["message"] == "Every task is complete."
