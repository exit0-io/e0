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


def test_cmd_verify_passes_for_a_correctly_personalized_file(run_e0, student_repo, write_task_file):
    run_e0(["init"], student_repo)
    write_task_file(student_repo, "T010", note="Skim this section.")
    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert "problem" not in payload


def test_cmd_verify_fails_when_fixed_text_is_altered(run_e0, student_repo, write_task_file):
    run_e0(["init"], student_repo)
    text = write_task_file(student_repo, "T010")
    task_file = student_repo / "content" / "t010" / "task.md"
    task_file.write_text(
        text.replace("**standard library**", "**requests library**"), encoding="utf-8"
    )
    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert "problem" in payload
    assert payload["data"]["violations"]
    assert "e0 task T010" in payload["guidance"]


def test_cmd_verify_before_the_file_exists_points_at_e0_task(run_e0, student_repo):
    run_e0(["init"], student_repo)
    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert "problem" in payload
    assert "e0 task T010" in payload["guidance"]

