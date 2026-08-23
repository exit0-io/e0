def test_init_downloads_catalog_and_writes_profile(run_e0, student_repo):
    payload, code = run_e0(["init"], student_repo)

    assert code == 0
    assert payload["ok"] is True
    assert (student_repo / ".exit0" / "catalog.json").exists()
    assert (student_repo / ".exit0" / "state" / "profile.json").exists()


def test_init_reports_course_title_and_task_count(run_e0, student_repo):
    payload, _ = run_e0(["init"], student_repo)
    assert payload["data"]["course"]["title"] == "Demo Course"
    assert payload["data"]["taskCount"] == 2


def test_init_installs_framework_skills(run_e0, student_repo):
    run_e0(["init"], student_repo)
    skills = student_repo / ".exit0" / "skills"
    assert (skills / "session.md").exists()
    assert (skills / "working-on-a-task.md").exists()


def test_init_installs_course_skills(run_e0, student_repo):
    run_e0(["init"], student_repo)
    assert (student_repo / ".exit0" / "skills" / "demo-course-notes.md").exists()


def test_init_creates_content_and_school_checks_dirs(run_e0, student_repo):
    run_e0(["init"], student_repo)
    assert (student_repo / "content").is_dir()
    assert (student_repo / "tests" / "school-checks").is_dir()


def test_init_is_idempotent(run_e0, student_repo):
    run_e0(["init"], student_repo)
    payload, code = run_e0(["init"], student_repo)
    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["taskCount"] == 2


def test_init_records_an_event(run_e0, student_repo, e0mod):
    run_e0(["init"], student_repo)
    events = e0mod.read_events(student_repo)
    assert any(event["event"] == "initialized" for event in events)


def test_init_without_course_content_repo_gives_guidance(run_e0, tmp_path):
    import subprocess
    bare = tmp_path / "no-config"
    bare.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(bare), check=True)
    (bare / ".exit0").mkdir()
    (bare / ".exit0" / "config.json").write_text("{}", encoding="utf-8")
    payload, code = run_e0(["init"], bare)
    assert code == 0
    assert payload["ok"] is False
    assert "courseContentRepo" in payload["guidance"]


def test_init_outside_a_git_repo_gives_guidance(run_e0, tmp_path):
    empty = tmp_path / "not-a-repo"
    empty.mkdir()
    payload, code = run_e0(["init"], empty)
    assert code == 0
    assert payload["ok"] is False
    assert payload["guidance"]
