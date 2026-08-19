import pytest


@pytest.fixture
def initialized(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
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


def test_status_reflects_recorded_events(run_e0, initialized, e0mod):
    e0mod.append_event(initialized, "task_started", taskId="T010")
    payload, _ = run_e0(["catalog"], initialized)
    statuses = {task["id"]: task["status"] for task in payload["data"]["tasks"]}
    assert statuses["T010"] == "in_progress"

    e0mod.append_event(initialized, "task_completed", taskId="T010")
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
    assert payload["ok"] is False
    assert "init" in payload["guidance"]
