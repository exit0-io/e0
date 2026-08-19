import json


def test_latest_tag_reads_the_newest_tag(e0mod, content_repo):
    assert e0mod.latest_tag(str(content_repo)) == "v0.1.0"


def test_latest_tag_on_an_unreachable_url_returns_none(e0mod, tmp_path):
    assert e0mod.latest_tag(str(tmp_path / "nope")) is None


def test_init_creates_the_exit0_tree(run_e0, student_repo, content_repo):
    payload, code = run_e0(
        ["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)}
    )

    assert code == 0
    assert payload["ok"] is True

    exit0 = student_repo / ".exit0"
    assert (exit0 / "course" / "catalog.json").exists()
    assert (exit0 / "state" / "profile.json").exists()
    assert (exit0 / "README.md").exists()


def test_init_finds_its_course_from_exit0_json(run_e0, student_repo, content_repo):
    """A fork reaches its content through exit0.json, so e0 ships separately from courses."""
    (student_repo / "exit0.json").write_text(
        json.dumps({"courseRepo": str(content_repo)}), encoding="utf-8"
    )
    payload, code = run_e0(["init"], student_repo)

    assert code == 0
    assert payload["ok"] is True
    assert payload["data"]["course"]["id"] == "demo"


def test_init_without_any_course_declaration_gives_guidance(run_e0, tmp_path):
    import subprocess

    bare = tmp_path / "bare"
    bare.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(bare), check=True)

    payload, code = run_e0(["init"], bare)
    assert code == 0
    assert payload["ok"] is False
    assert "exit0.json" in payload["guidance"]


def test_e0_supports_compares_versions(e0mod):
    assert e0mod.e0_supports("1.0") is True
    assert e0mod.e0_supports("0.9") is True
    assert e0mod.e0_supports("99.0") is False
    assert e0mod.e0_supports("") is True
    assert e0mod.e0_supports("nonsense") is True


def test_init_refuses_a_course_that_needs_a_newer_framework(
    run_e0, student_repo, make_course_repo
):
    def bump(catalog):
        catalog["requiresE0"] = "99.0"

    repo = make_course_repo(mutate_catalog=bump)
    payload, code = run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(repo)})

    assert code == 0
    assert payload["ok"] is False
    assert "99.0" in payload["problem"]
    assert "update" in payload["guidance"].lower()


def test_init_installs_framework_skills(
    run_e0, student_repo, content_repo, framework_dir
):
    payload, _ = run_e0(
        ["init"],
        student_repo,
        env={
            "E0_CONTENT_REPO": str(content_repo),
            "E0_SOURCE_DIR": str(framework_dir),
        },
    )
    assert payload["ok"] is True
    assert (student_repo / ".exit0" / "skills").is_dir()


def test_init_succeeds_even_when_the_framework_dir_is_missing(
    run_e0, student_repo, content_repo, tmp_path
):
    payload, code = run_e0(
        ["init"],
        student_repo,
        env={
            "E0_CONTENT_REPO": str(content_repo),
            "E0_SOURCE_DIR": str(tmp_path / "no-source-here"),
        },
    )
    assert code == 0
    assert payload["ok"] is True
    # No framework skills installed (dir was missing), but course skills may still be present.
    framework_skill_names = {"getting-started", "working-on-a-task", "using-the-knowledge-base"}
    installed = set(payload["data"]["skills"])
    assert installed.isdisjoint(framework_skill_names)


def test_init_reports_the_pinned_tag_and_course_title(run_e0, student_repo, content_repo):
    payload, _ = run_e0(
        ["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)}
    )
    assert payload["data"]["contentTag"] == "v0.1.0"
    assert payload["data"]["course"]["title"] == "Demo Course"


def test_init_adds_exit0_to_gitignore_without_touching_other_lines(
    run_e0, student_repo, content_repo
):
    gitignore = student_repo / ".gitignore"
    gitignore.write_text("*.pyc\n.venv/\n", encoding="utf-8")

    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})

    lines = gitignore.read_text(encoding="utf-8").splitlines()
    assert "*.pyc" in lines
    assert ".venv/" in lines
    assert ".exit0/" in lines


def test_init_does_not_duplicate_the_gitignore_entry(run_e0, student_repo, content_repo):
    env = {"E0_CONTENT_REPO": str(content_repo)}
    run_e0(["init"], student_repo, env=env)
    run_e0(["init"], student_repo, env=env)

    lines = (student_repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert lines.count(".exit0/") == 1


def test_init_is_idempotent(run_e0, student_repo, content_repo):
    env = {"E0_CONTENT_REPO": str(content_repo)}
    first, _ = run_e0(["init"], student_repo, env=env)
    second, code = run_e0(["init"], student_repo, env=env)

    assert code == 0
    assert second["ok"] is True
    assert first["data"]["contentTag"] == second["data"]["contentTag"]


def test_init_records_an_event(run_e0, student_repo, content_repo, e0mod):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    events = e0mod.read_events(student_repo)
    assert any(event["event"] == "initialized" for event in events)


def test_init_with_an_unreachable_course_repo_is_a_problem_not_a_crash(
    run_e0, student_repo, tmp_path
):
    payload, code = run_e0(
        ["init"], student_repo, env={"E0_CONTENT_REPO": str(tmp_path / "missing")}
    )
    assert code == 0
    assert payload["ok"] is False
    assert payload["guidance"]


def test_init_writes_a_warning_readme(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    readme = (student_repo / ".exit0" / "README.md").read_text(encoding="utf-8")
    assert "do not edit" in readme.lower()
