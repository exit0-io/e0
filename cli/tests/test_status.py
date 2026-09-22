import pytest


@pytest.fixture
def initialized(run_e0, student_repo):
    run_e0(["init"], student_repo)
    return student_repo


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
    assert payload["data"]["completed"] == ["T010"]
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


def test_status_when_all_tasks_complete(run_e0, initialized, set_issues):
    set_issues(initialized, [("T010", "CLOSED"), ("T020", "CLOSED")])
    payload, _ = run_e0(["status"], initialized)
    assert "problem" not in payload
    assert payload["data"]["inProgress"] == []
    assert payload["data"]["next"] == []
    assert payload["message"] == "Every task is complete."
