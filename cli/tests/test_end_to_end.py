import subprocess


def test_a_student_can_go_from_bootstrap_to_passing_checks(
    run_e0, student_repo, e0mod
):
    # 1. Agent bootstraps.
    payload, code = run_e0(["init"], student_repo)
    assert code == 0 and payload["ok"] is True
    assert payload["data"]["taskCount"] == 2

    # 2. Agent orients.
    payload, _ = run_e0(["status"], student_repo)
    assert payload["data"]["next"]["id"] == "T010"

    # 3. Student asks what the course covers.
    payload, _ = run_e0(["catalog"], student_repo)
    assert [t["id"] for t in payload["data"]["tasks"]] == ["T010", "T020"]

    # 4. Agent starts the first task.
    payload, _ = run_e0(["start", "T010"], student_repo)
    assert payload["data"]["warnings"] == []
    canonical = payload["data"]["canonical"]
    assert canonical

    # 5. Agent personalizes: strip markers, pick a branch, write clean Markdown.
    regions = e0mod.parse_regions(canonical)
    facts = payload["data"]["personalization"]["facts"]
    clean_parts = []
    for r in regions:
        if r["kind"] == "fixed":
            clean_parts.append(r["text"])
        elif r["kind"] == "variant":
            chosen = e0mod.select_branch(r["branches"], facts)
            clean_parts.append((chosen["text"] if chosen else r["branches"][0]["text"]) + "\n")
        else:
            clean_parts.append("Skim this.\n")
    task_dir = student_repo / "content" / "t010"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.md").write_text("".join(clean_parts), encoding="utf-8")

    # 6. Verify accepts the personalization.
    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0 and payload["ok"] is True

    # 7. Checks fail before any code is written.
    payload, _ = run_e0(["check", "T010"], student_repo)
    assert payload["data"]["passed"] is False

    # 8. Student writes the code.
    (student_repo / "greeting.py").write_text(
        'def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8"
    )

    # 9. Checks pass.
    payload, code = run_e0(["check", "T010"], student_repo)
    assert code == 0 and payload["ok"] is True
    assert payload["data"]["passed"] is True

    # 10. Nothing in .exit0/ leaked into git status.
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(student_repo),
        capture_output=True,
        text=True,
    )
    tracked_changes = [line for line in proc.stdout.splitlines() if ".exit0" in line]
    assert tracked_changes == [], ".exit0/ must never appear in git status"


def test_verify_catches_altered_fixed_text(run_e0, student_repo):
    run_e0(["init"], student_repo)
    start_payload, _ = run_e0(["start", "T010"], student_repo)
    canonical = start_payload["data"]["canonical"]

    task_dir = student_repo / "content" / "t010"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.md").write_text(
        canonical.replace("**standard library**", "**the requests library**"),
        encoding="utf-8",
    )

    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert payload["data"]["violations"]


def test_every_command_survives_a_hostile_environment(run_e0, tmp_path):
    """No command may crash, whatever state it is run in."""
    empty = tmp_path / "empty"
    empty.mkdir()
    for command in ["status", "catalog", "start", "verify", "check", "read", "init", "help"]:
        payload, code = run_e0([command], empty)
        assert code == 0, f"{command} must exit 0"
        assert isinstance(payload["ok"], bool), f"{command} must return a bool ok"


