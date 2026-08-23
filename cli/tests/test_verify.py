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


def test_cmd_verify_passes_for_correct_personalized_file(run_e0, student_repo, e0mod):
    run_e0(["init"], student_repo)
    start_payload, _ = run_e0(["start", "T010"], student_repo)
    canonical = start_payload["data"]["canonical"]
    regions = e0mod.parse_regions(canonical)
    clean_parts = []
    for r in regions:
        if r["kind"] == "fixed":
            clean_parts.append(r["text"])
        elif r["kind"] == "variant":
            clean_parts.append(r["branches"][0]["text"] + "\n")
        else:
            clean_parts.append("Skim this section.\n")
    task_dir = student_repo / "content" / "t010"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.md").write_text("".join(clean_parts), encoding="utf-8")
    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert payload["ok"] is True


def test_cmd_verify_fails_when_fixed_text_is_altered(run_e0, student_repo):
    run_e0(["init"], student_repo)
    start_payload, _ = run_e0(["start", "T010"], student_repo)
    canonical = start_payload["data"]["canonical"]
    task_dir = student_repo / "content" / "t010"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.md").write_text(
        canonical.replace("**standard library**", "**requests library**"),
        encoding="utf-8",
    )
    payload, code = run_e0(["verify", "T010"], student_repo)
    assert code == 0
    assert payload["ok"] is False
    assert payload["data"]["violations"]

