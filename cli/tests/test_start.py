import pytest


@pytest.fixture
def initialized(run_e0, student_repo):
    run_e0(["init"], student_repo)
    return student_repo


def test_start_writes_task_and_canonical_copies(run_e0, initialized):
    payload, code = run_e0(["start", "T010"], initialized)

    assert code == 0
    assert payload["ok"] is True

    task_dir = initialized / ".exit0" / "tasks" / "t010"
    assert (task_dir / "task.md").exists()
    assert (task_dir / "task.canonical.md").exists()
    assert (task_dir / "task.md").read_text(encoding="utf-8") == (
        task_dir / "task.canonical.md"
    ).read_text(encoding="utf-8")


def test_start_copies_the_check_files(run_e0, initialized):
    run_e0(["start", "T010"], initialized)
    checks = initialized / ".exit0" / "tasks" / "t010" / "checks"
    assert (checks / "test_greeting.py").exists()
    assert (checks / "checks.json").exists()


def test_start_accepts_a_lowercase_task_id(run_e0, initialized):
    payload, _ = run_e0(["start", "t010"], initialized)
    assert payload["ok"] is True
    assert payload["data"]["taskId"] == "T010"


def test_start_emits_the_issue_title_and_body(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    assert payload["data"]["issue"]["title"] == "[T010] Say hello"
    assert "Say hello" in payload["data"]["issue"]["body"]


def test_start_emits_variants_with_their_branches(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    variants = payload["data"]["personalization"]["variants"]
    assert len(variants) == 1
    assert variants[0]["id"] == "run-tests"
    assert {tuple(sorted(b["when"].items())) for b in variants[0]["branches"]} == {
        (("os", "linux"),),
        (("os", "macos"),),
        (("os", "windows"),),
    }


def test_start_emits_retone_blocks(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    blocks = payload["data"]["personalization"]["retoneBlocks"]
    assert len(blocks) == 1
    assert blocks[0]["basedOn"] == "the student's Python experience"


def test_start_emits_only_facts_referenced_by_variants(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    facts = payload["data"]["personalization"]["facts"]
    assert set(facts) == {"os"}


def test_start_includes_the_decoded_rules(run_e0, initialized):
    payload, _ = run_e0(["start", "T010"], initialized)
    assert "function" in payload["data"]["rules"]


def test_start_warns_about_unmet_dependencies_but_proceeds(run_e0, initialized):
    payload, code = run_e0(["start", "T020"], initialized)

    assert code == 0
    assert payload["ok"] is True
    warnings = payload["data"]["warnings"]
    assert any(warning["kind"] == "dependency" for warning in warnings)
    assert (initialized / ".exit0" / "tasks" / "t020" / "task.md").exists()


def test_start_records_an_override_event_for_unmet_dependencies(
    run_e0, initialized, e0mod
):
    run_e0(["start", "T020"], initialized)
    events = e0mod.read_events(initialized)
    assert any(event["event"] == "override" for event in events)


def test_start_records_a_task_started_event(run_e0, initialized, e0mod):
    run_e0(["start", "T010"], initialized)
    events = e0mod.read_events(initialized)
    started = [event for event in events if event["event"] == "task_started"]
    assert started and started[-1]["taskId"] == "T010"


def test_start_with_an_unknown_task_lists_valid_ids(run_e0, initialized):
    payload, code = run_e0(["start", "T999"], initialized)
    assert code == 0
    assert payload["ok"] is False
    assert "T010" in payload["guidance"]


def test_start_without_a_task_id_is_a_problem(run_e0, initialized):
    payload, code = run_e0(["start"], initialized)
    assert code == 0
    assert payload["ok"] is False


def test_start_does_not_overwrite_an_existing_personalized_task(run_e0, initialized):
    run_e0(["start", "T010"], initialized)
    task_file = initialized / ".exit0" / "tasks" / "t010" / "task.md"
    task_file.write_text("personalized already\n", encoding="utf-8")

    payload, _ = run_e0(["start", "T010"], initialized)

    assert task_file.read_text(encoding="utf-8") == "personalized already\n"
    assert payload["data"]["alreadyStarted"] is True


def test_read_command_gives_guidance_and_index_location(run_e0, initialized):
    payload, code = run_e0(["read", "intro-to-linux"], initialized)
    assert code == 0
    assert payload["ok"] is False
    assert "intro-to-linux" in payload["message"]


def test_profile_get_on_fresh_repo_detects_os(run_e0, student_repo):
    payload, code = run_e0(["profile", "get"], student_repo)
    assert code == 0
    assert payload["ok"] is True
    assert "os" in payload["data"]["profile"]
