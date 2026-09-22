def test_init_downloads_catalog_and_writes_profile(run_e0, student_repo):
    payload, code = run_e0(["init"], student_repo)

    assert code == 0
    assert "problem" not in payload
    assert (student_repo / ".exit0" / "catalog.json").exists()
    assert (student_repo / ".exit0" / "state" / "profile.json").exists()


def test_init_reports_course_title_and_task_count(run_e0, student_repo):
    payload, _ = run_e0(["init"], student_repo)
    assert payload["data"]["course"]["title"] == "Demo Course"
    assert payload["data"]["taskCount"] == 2


def test_init_creates_content_and_school_checks_dirs(run_e0, student_repo):
    run_e0(["init"], student_repo)
    assert (student_repo / "content").is_dir()
    assert (student_repo / "tests" / "school-checks").is_dir()


def test_init_is_idempotent(run_e0, student_repo):
    run_e0(["init"], student_repo)
    payload, code = run_e0(["init"], student_repo)
    assert code == 0
    assert "problem" not in payload
    assert payload["data"]["taskCount"] == 2


def test_init_keeps_only_the_profile_as_local_state(run_e0, student_repo):
    run_e0(["init"], student_repo)
    state = student_repo / ".exit0" / "state"
    assert [p.name for p in state.iterdir()] == ["profile.json"]


def test_init_without_course_content_repo_gives_guidance(run_e0, tmp_path):
    import subprocess
    bare = tmp_path / "no-config"
    bare.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(bare), check=True)
    (bare / ".exit0").mkdir()
    (bare / ".exit0" / "config.json").write_text("{}", encoding="utf-8")
    payload, code = run_e0(["init"], bare)
    assert code == 0
    assert "problem" in payload
    assert "courseContentRepo" in payload["guidance"]


def test_init_outside_a_git_repo_gives_guidance(run_e0, tmp_path):
    empty = tmp_path / "not-a-repo"
    empty.mkdir()
    payload, code = run_e0(["init"], empty)
    assert code == 0
    assert "problem" in payload
    assert payload["guidance"]


def test_init_installs_the_learning_skill_with_its_references(run_e0, student_repo):
    run_e0(["init"], student_repo)
    skills = student_repo / ".exit0" / "skills"
    assert (skills / "learning" / "SKILL.md").exists()
    assert (skills / "learning" / "references" / "setup-and-update.md").exists()
    assert not (skills / "setup-and-update").exists()


def test_init_output_is_only_what_the_student_needs_to_hear(run_e0, student_repo):
    """Skills are an implementation detail. The envelope names the course, the machine, the size."""
    payload, _ = run_e0(["init"], student_repo)
    assert set(payload["data"]) == {"course", "profile", "taskCount"}
