import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILLS = ROOT / "cli" / "skills"
E0_PATH = ROOT / "cli" / "bin" / "e0"

# The learning skill is the single entry point. Everything else is a reference inside it.
EXPECTED = {"learning"}
SETUP_REFERENCE = SKILLS / "learning" / "references" / "setup-and-update.md"

# Courses hosted by e0. None of these may appear in the CLI or in a framework skill.
COURSE_NAMES = ("polybot", "yoloservice", "mit2026", "polyaidev", "demo course")


def skill_files():
    return list(SKILLS.glob("*/SKILL.md")) + list(SKILLS.glob("*/references/*.md"))


def test_every_expected_skill_exists():
    present = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert present == EXPECTED


def test_every_framework_skill_file_e0_downloads_exists(e0mod):
    for name, files in e0mod.FRAMEWORK_SKILLS.items():
        for relative in files:
            assert (SKILLS / name / relative).exists(), f"missing {name}/{relative}"


def test_e0_downloads_every_skill_file_that_exists(e0mod):
    """A skill file that e0 does not know about would never reach the student."""
    for path in skill_files():
        name = path.relative_to(SKILLS).parts[0]
        relative = path.relative_to(SKILLS / name).as_posix()
        assert relative in e0mod.FRAMEWORK_SKILLS.get(name, []), f"e0 does not download {name}/{relative}"


def test_skills_only_reference_real_commands():
    source = E0_PATH.read_text(encoding="utf-8")
    registered = set(re.findall(r'^\s{4}"([a-z-]+)": cmd_', source, re.MULTILINE))
    for path in skill_files():
        mentioned = set(re.findall(r"`e0 ([a-z-]+)", path.read_text(encoding="utf-8")))
        assert mentioned <= registered, f"{path} references unknown: {mentioned - registered}"


def test_the_framework_names_no_course():
    """One e0 serves every course, so it must not hardcode any of them."""
    targets = [E0_PATH, *skill_files()]
    for path in targets:
        text = path.read_text(encoding="utf-8").lower()
        for name in COURSE_NAMES:
            assert name not in text, f"{path} names the course '{name}'"


def test_learning_skill_checks_for_e0_before_running_status():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert ".exit0/e0" in text
    assert "references/setup-and-update.md" in text
    assert text.index("references/setup-and-update.md") < text.index("e0 status")


def test_learning_skill_has_the_agent_personalize_silently():
    """The spec's personalization contract, done by the agent, never narrated to the student."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "data.canonical" in text
    assert "data.personalization" in text and "variants" in text
    assert "retone" in text
    assert "hears nothing about it" in text
    assert "Every other character stays as it is" in text
    assert text.index("e0 task <id>") < text.index("e0 start <id>") < text.index("e0 verify <id>")


def test_learning_skill_reads_progress_from_github_issues():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "open issue" in text.lower()
    assert "gh auth login" in text


def test_setup_reference_has_the_bootstrap_and_points_back():
    text = SETUP_REFERENCE.read_text(encoding="utf-8")
    assert "curl" in text
    assert ".exit0/e0 init" in text
    assert "learning" in text


def test_setup_reference_mentions_the_cheap_model():
    text = SETUP_REFERENCE.read_text(encoding="utf-8").lower()
    assert "cheap" in text or "cheapest" in text


def test_setup_reference_falls_back_to_the_latest_release():
    """A pinned tag that was never published must not stop a student. Latest is the net."""
    text = SETUP_REFERENCE.read_text(encoding="utf-8")
    assert "releases/latest/download/e0" in text
    assert text.count("releases/latest/download/e0") >= 2, "bash and PowerShell both need it"


def test_learning_skill_separates_looking_at_a_task_from_starting_it():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "e0 task" in text
    assert text.index("e0 task") < text.index("e0 start <id>")
    assert "preview" in text.lower(), "students must be told how to read Markdown"
    assert "](content/" in text, "file links must be clickable"


def test_learning_skill_names_the_protocol_and_its_shortcuts():
    """From conversation.md: the agent must know the road (issue, branch, PR, merge, close,
    questions) and say so when a closed issue has no merged PR."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "## The protocol" in text
    for step in ("Issue", "Branch", "Implement", "Pull request", "close the issue", "Comprehension"):
        assert step in text, f"protocol step missing: {step}"
    assert "closed_without_pr" in text
    assert "reopen" in text


def test_learning_skill_sends_the_student_to_a_branch_first():
    """From conversation.md: after handing over the task, the first move is a feature branch
    from an updated main, run by the student."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "git checkout -b" in text
    assert "git pull" in text
    assert "first move" in text


def test_learning_skill_links_the_issue_url():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "issue URL" in text


def test_setup_reference_has_no_permission_nag():
    """From conversation.md: the 'allow e0 to run without asking' note is gone."""
    text = SETUP_REFERENCE.read_text(encoding="utf-8").lower()
    assert "without asking" not in text
    assert "allow" not in text


def test_learning_skill_stays_compact():
    """A stated goal: the skill is as short as it can be. Raise this bound only on purpose."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 100, "SKILL.md grew; prune before adding"
    assert len(text) <= 7000


def test_release_workflow_publishes_the_pinned_version():
    """Every push to main that changes e0 must create the tag the skill downloads."""
    workflow = ROOT / ".github" / "workflows" / "release.yml"
    assert workflow.exists()
    text = workflow.read_text(encoding="utf-8")
    assert "E0_VERSION" in text
    assert "gh release create" in text
    assert "cli/bin/e0" in text


def test_the_pinned_version_matches_every_release_the_setup_reference_downloads():
    """Both name the same git tag: e0 fetches its skills from the ref it was released as."""
    setup = SETUP_REFERENCE.read_text(encoding="utf-8")
    releases = set(re.findall(r'RELEASE="?(v[0-9][0-9.]*)"?', setup))
    version = re.search(r'^E0_VERSION = "(\S+)"', E0_PATH.read_text(encoding="utf-8"), re.MULTILINE).group(1)
    assert releases, "the setup reference must pin a release"
    assert releases == {version}
