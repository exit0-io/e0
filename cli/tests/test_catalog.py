import pytest


@pytest.fixture
def initialized(run_e0, student_repo):
    run_e0(["init"], student_repo)
    return student_repo


def test_catalog_lists_every_task_in_order(run_e0, initialized):
    payload, code = run_e0(["catalog"], initialized)
    assert code == 0
    assert [task["id"] for task in payload["data"]["tasks"]] == ["T010", "T020"]


def test_catalog_reports_dependencies_and_status(run_e0, initialized):
    payload, _ = run_e0(["catalog"], initialized)
    second = payload["data"]["tasks"][1]
    assert second["dependsOn"] == ["T010"]
    assert second["status"] == "not_started"


def test_catalog_passes_every_author_field_through(run_e0, initialized, e0mod):
    """New catalog fields (purpose, learning goals, ...) must reach the agent with no e0 change."""
    payload, _ = run_e0(["catalog"], initialized)
    source = e0mod.read_catalog(initialized)
    for task, original in zip(payload["data"]["tasks"], source["tasks"]):
        for key, value in original.items():
            assert task[key] == value
    assert payload["data"]["course"]["title"] == "Demo Course"
    assert "contentTag" not in payload["data"]


def test_catalog_status_reflects_the_github_issues(run_e0, initialized, set_issues):
    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["catalog"], initialized)
    statuses = {task["id"]: task["status"] for task in payload["data"]["tasks"]}
    assert statuses["T010"] == "in_progress"

    set_issues(initialized, [("T010", "CLOSED")])
    payload, _ = run_e0(["catalog"], initialized)
    statuses = {task["id"]: task["status"] for task in payload["data"]["tasks"]}
    assert statuses["T010"] == "complete"


def test_find_task_is_case_insensitive(e0mod, initialized):
    catalog = e0mod.read_catalog(initialized)
    assert e0mod.find_task(catalog, "t010")["id"] == "T010"
    assert e0mod.find_task(catalog, "T010")["id"] == "T010"
    assert e0mod.find_task(catalog, "T999") is None


def test_catalog_before_init_gives_guidance(run_e0, student_repo):
    payload, code = run_e0(["catalog"], student_repo)
    assert code == 0
    assert "problem" in payload
    assert "init" in payload["guidance"]
