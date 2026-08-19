import json
import pathlib
import re

TEMPLATE = (
    pathlib.Path(__file__).resolve().parents[2] / "courses" / "demo" / "template"
)
E0_PATH = pathlib.Path(__file__).resolve().parents[1] / "bin" / "e0"


def test_template_has_the_required_files():
    for name in (
        "README.md",
        "AGENTS.md",
        "CLAUDE.md",
        "exit0.json",
        ".github/copilot-instructions.md",
        ".gitignore",
    ):
        assert (TEMPLATE / name).exists(), f"missing {name}"


def test_exit0_json_names_the_course_content_repo():
    """This file is the only thing tying a fork to its course content."""
    declaration = json.loads((TEMPLATE / "exit0.json").read_text(encoding="utf-8"))
    assert declaration["courseRepo"].startswith("http")
    assert declaration["courseRepo"].endswith(".git")


def test_readme_tells_the_student_to_say_hi():
    readme = (TEMPLATE / "README.md").read_text(encoding="utf-8").lower()
    assert "fork" in readme
    assert "hi" in readme


def test_readme_does_not_ask_the_student_to_install_anything():
    readme = (TEMPLATE / "README.md").read_text(encoding="utf-8").lower()
    for forbidden in ("pip install", "npm install", "brew install", "apt install"):
        assert forbidden not in readme


def test_agents_md_bootstraps_the_framework_before_using_it():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    bootstrap_at = agents.find(".exit0/bin/e0")
    status_at = agents.find("e0 status")
    assert bootstrap_at != -1, "AGENTS.md must describe fetching the framework"
    assert status_at != -1
    assert bootstrap_at < status_at, "bootstrap must come before any e0 usage"


def test_pointer_files_redirect_to_agents_md():
    for name in ("CLAUDE.md", ".github/copilot-instructions.md"):
        text = (TEMPLATE / name).read_text(encoding="utf-8")
        assert "AGENTS.md" in text
        assert len(text.splitlines()) <= 6, f"{name} should be a pointer, not a copy"


def test_gitignore_excludes_exit0():
    lines = (TEMPLATE / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".exit0/" in lines


def test_every_e0_command_agents_md_mentions_actually_exists():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    source = E0_PATH.read_text(encoding="utf-8")
    registered = set(re.findall(r'^\s{4}"([a-z-]+)": cmd_', source, re.MULTILINE))
    mentioned = set(re.findall(r"`e0 ([a-z-]+)", agents))
    assert mentioned <= registered, f"AGENTS.md mentions unknown commands: {mentioned - registered}"
