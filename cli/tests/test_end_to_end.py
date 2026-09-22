import subprocess


def test_a_student_can_go_from_bootstrap_to_passing_checks(
    run_e0, student_repo, personalize, set_issues
):
    # 1. Agent bootstraps.
    payload, code = run_e0(["init"], student_repo)
    assert code == 0 and "problem" not in payload
    assert payload["data"]["taskCount"] == 2

    # 2. Agent orients. No issues yet, so nothing is in progress.
    payload, _ = run_e0(["status"], student_repo)
    assert [t["id"] for t in payload["data"]["next"]] == ["T010"]

    # 3. Student asks what the course covers.
    payload, _ = run_e0(["catalog"], student_repo)
    assert [t["id"] for t in payload["data"]["tasks"]] == ["T010", "T020"]

    # 4. Student asks about the first task. The agent fetches it and, silently,
    #    personalizes it: one variant branch, no markers, a note where retone allows it.
    payload, _ = run_e0(["task", "T010"], student_repo)
    assert payload["data"]["task"]["purpose"]
    text = personalize(payload, note="You know Python well, so this will be quick.")
    task_file = student_repo / "content" / "t010" / "task.md"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    task_file.write_text(text, encoding="utf-8")
    assert "<!--" not in text

    # 5. Student asks to start. e0 checks the file and hands back the issue.
    payload, _ = run_e0(["start", "T010"], student_repo)
    assert "problem" not in payload, payload
    assert payload["data"]["warnings"] == []
    assert payload["data"]["issue"]["body"] == text

    # 6. The agent opens the issue. From now on that issue is the progress record.
    set_issues(student_repo, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], student_repo)
    assert [t["id"] for t in payload["data"]["inProgress"]] == ["T010"]

    # 7. Checks fail before any code is written. `check` finds the in-progress task itself.
    payload, _ = run_e0(["check"], student_repo)
    assert payload["data"]["taskId"] == "T010"
    assert payload["data"]["passed"] is False

    # 8. Student writes the code.
    (student_repo / "greeting.py").write_text(
        'def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8"
    )

    # 9. Checks pass.
    payload, code = run_e0(["check", "T010"], student_repo)
    assert code == 0 and "problem" not in payload
    assert payload["data"]["passed"] is True

    # 10. The student closes the issue. T010 is complete and T020 is unlocked.
    set_issues(student_repo, [("T010", "CLOSED")])
    payload, _ = run_e0(["status"], student_repo)
    assert payload["data"]["completed"] == ["T010"]
    assert [t["id"] for t in payload["data"]["next"]] == ["T020"]

    # 11. Nothing in .exit0/ leaked into git status.
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(student_repo),
        capture_output=True,
        text=True,
    )
    tracked_changes = [line for line in proc.stdout.splitlines() if ".exit0" in line]
    assert tracked_changes == [], ".exit0/ must never appear in git status"


def test_verify_catches_altered_fixed_text(run_e0, student_repo, write_task_file):
    run_e0(["init"], student_repo)
    text = write_task_file(student_repo, "T010")
    task_file = student_repo / "content" / "t010" / "task.md"
    task_file.write_text(
        text.replace("**standard library**", "**the requests library**"), encoding="utf-8"
    )

    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert "problem" in payload
    assert payload["data"]["violations"]


def test_every_command_survives_a_hostile_environment(run_e0, tmp_path):
    """No command may crash, whatever state it is run in."""
    empty = tmp_path / "empty"
    empty.mkdir()
    for command in ["status", "catalog", "task", "start", "verify", "check", "read", "init", "help"]:
        payload, code = run_e0([command], empty)
        assert code == 0, f"{command} must exit 0"
        assert "command" in payload, f"{command} must return an envelope"
