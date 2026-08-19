import json
import subprocess


def test_a_student_can_go_from_fork_to_passing_checks(
    run_e0, student_repo, content_repo, e0mod
):
    env = {"E0_CONTENT_REPO": str(content_repo)}

    # 1. The agent bootstraps the course.
    payload, code = run_e0(["init"], student_repo, env=env)
    assert code == 0 and payload["ok"] is True
    assert payload["data"]["taskCount"] == 2

    # 2. The agent orients itself.
    payload, _ = run_e0(["status"], student_repo, env=env)
    assert payload["data"]["next"]["id"] == "T010"
    assert payload["data"]["current"] is None

    # 3. The student asks what the course covers.
    payload, _ = run_e0(["catalog"], student_repo, env=env)
    assert [task["id"] for task in payload["data"]["tasks"]] == ["T010", "T020"]

    # 4. The agent starts the first task.
    payload, _ = run_e0(["start", "T010"], student_repo, env=env)
    assert payload["data"]["warnings"] == []
    facts = payload["data"]["personalization"]["facts"]
    variant = payload["data"]["personalization"]["variants"][0]

    # 5. The agent personalizes: pick the matching branch, drop the rest.
    task_file = student_repo / ".exit0" / "tasks" / "t010" / "task.md"
    chosen = e0mod.select_branch(variant["branches"], facts)
    assert chosen is not None
    original = task_file.read_text(encoding="utf-8")
    start = original.index('<!-- e0:variant id="run-tests" -->')
    end = original.index("<!-- /e0:variant -->") + len("<!-- /e0:variant -->\n")
    personalized = (
        original[:start]
        + '<!-- e0:variant id="run-tests" -->\n'
        + chosen["text"]
        + "\n<!-- /e0:variant -->\n"
        + original[end:]
    )
    task_file.write_text(personalized, encoding="utf-8")

    # 6. Verification accepts a legal personalization.
    payload, code = run_e0(["verify", "T010"], student_repo, env=env)
    assert code == 0 and payload["ok"] is True

    # 7. Checks fail before any code is written.
    payload, _ = run_e0(["check", "T010"], student_repo, env=env)
    assert payload["data"]["passed"] is False

    # 8. The student writes the code.
    (student_repo / "greeting.py").write_text(
        'def greet(name):\n    return f"Hello, {name}!"\n', encoding="utf-8"
    )

    # 9. Checks pass.
    payload, code = run_e0(["check", "T010"], student_repo, env=env)
    assert code == 0 and payload["ok"] is True
    assert payload["data"]["passed"] is True

    # 10. Nothing leaked into the student's git status.
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(student_repo),
        capture_output=True,
        text=True,
    )
    tracked_changes = [
        line for line in proc.stdout.splitlines() if ".exit0" in line
    ]
    assert tracked_changes == [], ".exit0/ must never appear in git status"


def test_pedagogical_drift_is_caught_and_reverted(run_e0, student_repo, content_repo):
    env = {"E0_CONTENT_REPO": str(content_repo)}
    run_e0(["init"], student_repo, env=env)
    run_e0(["start", "T010"], student_repo, env=env)

    task_file = student_repo / ".exit0" / "tasks" / "t010" / "task.md"
    task_file.write_text(
        task_file.read_text(encoding="utf-8").replace(
            "**standard library**", "**the requests library, which is nicer**"
        ),
        encoding="utf-8",
    )

    payload, code = run_e0(["verify", "T010"], student_repo, env=env)

    assert code == 0
    assert payload["ok"] is False
    restored = task_file.read_text(encoding="utf-8")
    assert "**standard library**" in restored
    assert "requests" not in restored


def test_every_command_survives_a_hostile_environment(run_e0, tmp_path, e0mod):
    """No command may crash, whatever state it is run in."""
    empty = tmp_path / "empty"
    empty.mkdir()

    invocations = [
        ["init"],
        ["status"],
        ["catalog"],
        ["start"],
        ["start", "NOPE"],
        ["verify"],
        ["verify", "NOPE"],
        ["check"],
        ["check", "NOPE"],
        ["profile", "get"],
        ["profile", "set"],
        ["profile", "nonsense"],
        ["help"],
        [],
        ["--version"],
        [""],
    ]

    for args in invocations:
        payload, code = run_e0(args, empty)
        assert code == 0, f"{args} exited {code}"
        assert isinstance(payload.get("ok"), bool), f"{args} produced no envelope"
        if payload["ok"] is False:
            assert payload["guidance"], f"{args} gave no guidance"
