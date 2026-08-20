def test_init_writes_profile_and_creates_tasks_dir(run_e0, student_repo):
    payload, code = run_e0(["init"], student_repo)

    assert code == 0
    assert payload["ok"] is True
    assert (student_repo / ".exit0" / "e0" / "state" / "profile.json").exists()
    assert (student_repo / ".exit0" / "tasks").is_dir()


def test_init_reports_course_title_and_task_count(run_e0, student_repo):
    payload, _ = run_e0(["init"], student_repo)
    assert payload["data"]["course"]["title"] == "Demo Course"
    assert payload["data"]["taskCount"] == 2


def test_init_when_submodule_not_initialized_gives_guidance(run_e0, bare_student_repo):
    payload, code = run_e0(["init"], bare_student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert "submodule" in payload["guidance"].lower()


def test_init_is_idempotent(run_e0, student_repo):
    first, _ = run_e0(["init"], student_repo)
    second, code = run_e0(["init"], student_repo)
    assert code == 0
    assert second["ok"] is True
    assert first["data"]["taskCount"] == second["data"]["taskCount"]


def test_init_records_an_event(run_e0, student_repo, e0mod):
    run_e0(["init"], student_repo)
    events = e0mod.read_events(student_repo)
    assert any(event["event"] == "initialized" for event in events)


def test_init_outside_a_git_repo_gives_guidance(run_e0, tmp_path):
    empty = tmp_path / "not-a-repo"
    empty.mkdir()
    payload, code = run_e0(["init"], empty)
    assert code == 0
    assert payload["ok"] is False
    assert payload["guidance"]
