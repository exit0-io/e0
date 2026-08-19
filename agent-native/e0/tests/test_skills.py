import pathlib
import re

SKILLS = pathlib.Path(__file__).resolve().parents[1] / "skills"
E0_PATH = pathlib.Path(__file__).resolve().parents[1] / "bin" / "e0"

EXPECTED = {"getting-started", "working-on-a-task", "using-the-knowledge-base"}

# Courses hosted by e0. None of these may appear in the CLI or in a framework skill.
COURSE_NAMES = ("polybot", "yoloservice", "mit2026", "polyaidev", "demo course")


def test_every_expected_skill_exists():
    present = {path.stem for path in SKILLS.glob("*.md")}
    assert EXPECTED <= present


def test_skills_only_reference_real_commands():
    source = E0_PATH.read_text(encoding="utf-8")
    registered = set(re.findall(r'^\s{4}"([a-z-]+)": cmd_', source, re.MULTILINE))
    for path in SKILLS.glob("*.md"):
        mentioned = set(re.findall(r"`e0 ([a-z-]+)", path.read_text(encoding="utf-8")))
        assert mentioned <= registered, f"{path.name} references unknown: {mentioned - registered}"


def test_the_framework_names_no_course():
    """One e0 serves every course, so it must not hardcode any of them."""
    targets = [E0_PATH, *SKILLS.glob("*.md")]
    for path in targets:
        text = path.read_text(encoding="utf-8").lower()
        for name in COURSE_NAMES:
            assert name not in text, f"{path.name} names the course '{name}'"


def test_working_on_a_task_requires_verify_after_personalizing():
    text = (SKILLS / "working-on-a-task.md").read_text(encoding="utf-8")
    assert "e0 verify" in text
    assert text.index("e0 start") < text.index("e0 verify")


def test_getting_started_mentions_the_cheap_model():
    text = (SKILLS / "getting-started.md").read_text(encoding="utf-8").lower()
    assert "cheap" in text or "cheapest" in text


def test_init_installs_framework_skills_and_layers_course_skills(
    run_e0, student_repo, content_repo, framework_dir
):
    run_e0(
        ["init"],
        student_repo,
        env={
            "E0_CONTENT_REPO": str(content_repo),
            "E0_SOURCE_DIR": str(framework_dir),
        },
    )
    delivered = {
        path.stem for path in (student_repo / ".exit0" / "skills").glob("*.md")
    }
    assert EXPECTED <= delivered, "framework skills must be installed"
    assert "demo-course-notes" in delivered, "course skills must layer on top"
