import pytest


@pytest.fixture
def initialized(run_e0, student_repo):
    run_e0(["init"], student_repo)
    return student_repo


def test_status_on_a_fresh_course_suggests_the_first_task(run_e0, initialized):
    payload, code = run_e0(["status"], initialized)
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["next"]["id"] == "T010"
    assert payload["data"]["current"] is None


def test_status_reports_the_task_in_progress(run_e0, initialized, e0mod):
    e0mod.append_event(initialized, "task_started", taskId="T010")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["current"]["id"] == "T010"


def test_next_task_skips_completed_work(e0mod, initialized):
    catalog = e0mod.read_catalog(initialized)
    statuses = {"T010": "complete"}
    assert e0mod.next_task(catalog, statuses)["id"] == "T020"


def test_next_task_is_none_when_everything_is_done(e0mod, initialized):
    catalog = e0mod.read_catalog(initialized)
    statuses = {"T010": "complete", "T020": "complete"}
    assert e0mod.next_task(catalog, statuses) is None


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


def test_status_before_init_gives_guidance(run_e0, bare_student_repo):
    payload, code = run_e0(["status"], bare_student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "init" in payload["guidance"]


def test_status_when_all_tasks_complete(run_e0, initialized, e0mod):
    e0mod.append_event(initialized, "task_completed", taskId="T010")
    e0mod.append_event(initialized, "task_completed", taskId="T020")
    payload, _ = run_e0(["status"], initialized)
    assert payload["ok"] is True
    assert payload["data"]["current"] is None
    assert payload["data"]["next"] is None
