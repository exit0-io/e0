import pytest


@pytest.fixture
def initialized(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
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


def test_status_reports_update_availability_as_a_string(run_e0, initialized, content_repo):
    payload, _ = run_e0(
        ["status"], initialized, env={"E0_CONTENT_REPO": str(content_repo)}
    )
    assert payload["data"]["update"] in {"current", "available", "unknown"}


def test_status_says_unknown_when_the_course_repo_is_unreachable(
    run_e0, initialized, tmp_path
):
    payload, code = run_e0(
        ["status"], initialized, env={"E0_CONTENT_REPO": str(tmp_path / "gone")}
    )
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["update"] == "unknown"


def test_bare_e0_runs_status(run_e0, initialized):
    payload, code = run_e0([], initialized)
    assert code == 0
    assert payload["command"] == "status"


def test_status_before_init_gives_guidance(run_e0, student_repo):
    payload, code = run_e0(["status"], student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "init" in payload["guidance"]
