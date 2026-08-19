import pytest

CANONICAL = """# Task

Build the agent using **langchain**.

<!-- e0:variant id="install" -->
<!-- when: os=macos -->
brew install ffmpeg
<!-- when: os=linux -->
sudo apt install ffmpeg
<!-- /e0:variant -->

<!-- e0:retone based-on="experience" -->
<!-- /e0:retone -->

Done.
"""


def _personalize(variant_body, retone_body, fixed_tail="Done.\n"):
    return (
        "# Task\n\nBuild the agent using **langchain**.\n\n"
        '<!-- e0:variant id="install" -->\n'
        f"{variant_body}"
        "<!-- /e0:variant -->\n\n"
        '<!-- e0:retone based-on="experience" -->\n'
        f"{retone_body}"
        "<!-- /e0:retone -->\n\n"
        f"{fixed_tail}"
    )


def test_unchanged_document_has_no_violations(e0mod):
    result = e0mod.verify_document(CANONICAL, CANONICAL)
    assert result["violations"] == []
    assert result["restored"] == CANONICAL


def test_selecting_a_declared_branch_is_allowed(e0mod):
    personalized = _personalize("sudo apt install ffmpeg\n", "")
    result = e0mod.verify_document(CANONICAL, personalized)
    assert result["violations"] == []


def test_inventing_a_branch_is_a_violation(e0mod):
    personalized = _personalize("nix-env -i ffmpeg\n", "")
    result = e0mod.verify_document(CANONICAL, personalized)
    assert len(result["violations"]) == 1
    assert result["violations"][0]["kind"] == "variant"
    assert result["violations"][0]["id"] == "install"


def test_filling_a_retone_block_is_allowed(e0mod):
    personalized = _personalize(
        "sudo apt install ffmpeg\n", "You have done this before, so skim it.\n"
    )
    result = e0mod.verify_document(CANONICAL, personalized)
    assert result["violations"] == []


def test_editing_fixed_prose_is_a_violation(e0mod):
    personalized = _personalize("sudo apt install ffmpeg\n", "").replace(
        "**langchain**", "**langgraph**"
    )
    result = e0mod.verify_document(CANONICAL, personalized)

    assert any(violation["kind"] == "fixed" for violation in result["violations"])
    assert "**langchain**" in result["restored"]
    assert "**langgraph**" not in result["restored"]


def test_restored_document_keeps_allowed_personalization(e0mod):
    personalized = _personalize(
        "sudo apt install ffmpeg\n", "Skim this.\n"
    ).replace("**langchain**", "**langgraph**")
    result = e0mod.verify_document(CANONICAL, personalized)

    assert "**langchain**" in result["restored"]
    assert "sudo apt install ffmpeg" in result["restored"]
    assert "Skim this." in result["restored"]


def test_deleting_a_region_is_a_violation(e0mod):
    personalized = "# Task\n\nBuild the agent using **langchain**.\n\nDone.\n"
    result = e0mod.verify_document(CANONICAL, personalized)
    assert any(violation["kind"] == "structure" for violation in result["violations"])
    assert result["restored"] == CANONICAL


def test_verify_command_restores_the_file_on_disk(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    run_e0(["start", "T010"], student_repo)

    task_file = student_repo / ".exit0" / "tasks" / "t010" / "task.md"
    tampered = task_file.read_text(encoding="utf-8").replace(
        "**standard library**", "**requests**"
    )
    task_file.write_text(tampered, encoding="utf-8")

    payload, code = run_e0(["verify", "T010"], student_repo)

    assert code == 0
    assert payload["ok"] is False
    assert payload["data"]["violations"]
    assert "**standard library**" in task_file.read_text(encoding="utf-8")


def test_verify_command_on_a_clean_document_passes(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    run_e0(["start", "T010"], student_repo)

    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert payload["ok"] is True


def test_verify_without_a_target_is_a_problem(run_e0, student_repo, content_repo):
    run_e0(["init"], student_repo, env={"E0_CONTENT_REPO": str(content_repo)})
    payload, code = run_e0(["verify"], student_repo)
    assert code == 0
    assert payload["ok"] is False
