import pytest

CANONICAL = """\
# Task

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

# A correctly personalized clean document — no markers, one variant branch selected.
PERSONALIZED_OK = """\
# Task

Build the agent using **langchain**.

brew install ffmpeg

You have done this before, so skim it.

Done.
"""

PERSONALIZED_ALTERED_FIXED = """\
# Task

Build the agent using **langgraph**.

brew install ffmpeg

Done.
"""


def test_clean_personalized_doc_has_no_violations(e0mod):
    result = e0mod.verify_document(CANONICAL, PERSONALIZED_OK)
    assert result["violations"] == []


def test_altering_fixed_prose_is_a_violation(e0mod):
    result = e0mod.verify_document(CANONICAL, PERSONALIZED_ALTERED_FIXED)
    assert any(v["kind"] == "fixed" for v in result["violations"])


def test_missing_fixed_chunk_is_a_violation(e0mod):
    personalized = PERSONALIZED_OK.replace("Done.\n", "")
    result = e0mod.verify_document(CANONICAL, personalized)
    assert any(v["kind"] == "fixed" for v in result["violations"])


def test_verify_document_returns_no_restored_key(e0mod):
    result = e0mod.verify_document(CANONICAL, PERSONALIZED_OK)
    assert "restored" not in result


def test_malformed_canonical_markers_are_a_structure_violation(e0mod):
    bad_canonical = '<!-- e0:variant id="x" -->\nno closer\n'
    result = e0mod.verify_document(bad_canonical, "anything")
    assert any(v["kind"] == "structure" for v in result["violations"])


def test_task_write_writes_a_correctly_personalized_file(run_e0, student_repo, personalize):
    run_e0(["init"], student_repo)
    payload, _ = run_e0(["task", "T010"], student_repo)
    text = personalize(payload, note="Skim this section.")
    payload, code = run_e0(["task", "T010", "--write"], student_repo, stdin=text)
    assert code == 0
    assert "problem" not in payload
    assert payload["data"]["path"] == "content/t010/task.md"
    assert (student_repo / "content" / "t010" / "task.md").read_text(encoding="utf-8") == text


def test_task_write_overwrites_an_old_task_file(run_e0, student_repo, write_task_file):
    run_e0(["init"], student_repo)
    task_file = student_repo / "content" / "t010" / "task.md"
    task_file.parent.mkdir(parents=True)
    task_file.write_text("an old file\n", encoding="utf-8")
    text = write_task_file(student_repo, "T010")
    assert task_file.read_text(encoding="utf-8") == text


def test_task_write_refuses_altered_fixed_text_and_writes_nothing(
    run_e0, student_repo, personalize
):
    run_e0(["init"], student_repo)
    payload, _ = run_e0(["task", "T010"], student_repo)
    text = personalize(payload).replace("**standard library**", "**requests library**")
    payload, code = run_e0(["task", "T010", "--write"], student_repo, stdin=text)
    assert code == 0
    assert "problem" in payload
    assert payload["data"]["violations"]
    assert "e0 task T010 --write" in payload["guidance"]
    assert not (student_repo / "content" / "t010" / "task.md").exists()


def test_task_write_without_input_is_a_problem(run_e0, student_repo):
    run_e0(["init"], student_repo)
    payload, code = run_e0(["task", "T010", "--write"], student_repo)
    assert code == 0
    assert "problem" in payload
    assert "e0 task T010 --write" in payload["guidance"]


def test_verify_is_not_a_command(run_e0, student_repo):
    """2026-10-07: checking the task file is part of `e0 task --write`, not its own command."""
    run_e0(["init"], student_repo)
    payload, _ = run_e0(["verify", "T010"], student_repo)
    assert "problem" in payload
