import pathlib
import re

SKILLS = pathlib.Path(__file__).resolve().parents[1] / "skills"
E0_PATH = pathlib.Path(__file__).resolve().parents[1] / "bin" / "e0"

EXPECTED = {"learning", "setup-and-update"}

# Courses hosted by e0. None of these may appear in the CLI or in a framework skill.
COURSE_NAMES = ("polybot", "yoloservice", "mit2026", "polyaidev", "demo course")


def test_every_expected_skill_exists():
    present = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert EXPECTED <= present


def test_skills_only_reference_real_commands():
    source = E0_PATH.read_text(encoding="utf-8")
    registered = set(re.findall(r'^\s{4}"([a-z-]+)": cmd_', source, re.MULTILINE))
    for path in SKILLS.glob("*/SKILL.md"):
        mentioned = set(re.findall(r"`e0 ([a-z-]+)", path.read_text(encoding="utf-8")))
        assert mentioned <= registered, f"{path.parent.name} references unknown: {mentioned - registered}"


def test_the_framework_names_no_course():
    """One e0 serves every course, so it must not hardcode any of them."""
    targets = [E0_PATH, *SKILLS.glob("*/SKILL.md")]
    for path in targets:
        text = path.read_text(encoding="utf-8").lower()
        for name in COURSE_NAMES:
            assert name not in text, f"{path.parent.name} names the course '{name}'"


def test_learning_skill_requires_verify_after_start():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "e0 verify" in text
    assert text.index("e0 start") < text.index("e0 verify")


def test_setup_skill_mentions_the_cheap_model():
    text = (SKILLS / "setup-and-update" / "SKILL.md").read_text(encoding="utf-8").lower()
    assert "cheap" in text or "cheapest" in text
