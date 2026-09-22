import filecmp
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "courses" / "demo" / "template"
FRAMEWORK_SKILLS = ROOT / "cli" / "skills"

LEARNING_SKILL = ".exit0/skills/learning/SKILL.md"


def test_template_has_required_files():
    for name in (
        "README.md",
        "AGENTS.md",
        "CLAUDE.md",
        ".github/copilot-instructions.md",
        ".exit0/config.json",
        LEARNING_SKILL,
        ".exit0/skills/learning/references/setup-and-update.md",
        ".gitignore",
    ):
        assert (TEMPLATE / name).exists(), f"missing {name}"


def test_exit0_json_removed():
    assert not (TEMPLATE / "exit0.json").exists(), "exit0.json must be removed"


def test_config_json_names_course_content_repo():
    config = json.loads((TEMPLATE / ".exit0" / "config.json").read_text(encoding="utf-8"))
    assert "courseContentRepo" in config
    assert "exit0-io" in config["courseContentRepo"]


def test_no_gitmodules_file():
    assert not (TEMPLATE / ".gitmodules").exists(), ".gitmodules must be removed"


def test_no_submodule_dirs():
    assert not (TEMPLATE / ".exit0" / "e0").exists()
    assert not (TEMPLATE / ".exit0" / "content").exists()


def test_gitignore_covers_generated_dirs():
    text = (TEMPLATE / ".gitignore").read_text(encoding="utf-8")
    # .exit0/* with exception covers catalog.json, skills/, state/
    assert ".exit0/*" in text or ".exit0/" in text
    for entry in ("content/", "tests/school-checks/"):
        assert entry in text, f".gitignore missing: {entry}"


def test_template_ships_only_the_learning_skill():
    """Before e0 exists the agent can only read what the template ships. One skill, nothing else."""
    shipped = {p.name for p in (TEMPLATE / ".exit0" / "skills").iterdir()}
    assert shipped == {"learning"}


def test_template_learning_skill_is_identical_to_the_framework_copy():
    """e0 init overwrites the shipped copy with the released one. They must match, or the
    student sees an unexplained change in their git tab."""
    result = filecmp.dircmp(FRAMEWORK_SKILLS / "learning", TEMPLATE / ".exit0" / "skills" / "learning")
    differences = []

    def collect(cmp, prefix=""):
        differences.extend(prefix + n for n in cmp.left_only + cmp.right_only + cmp.diff_files)
        for sub, subcmp in cmp.subdirs.items():
            collect(subcmp, prefix + sub + "/")

    collect(result)
    assert differences == [], f"template skill differs from framework: {differences}"


def test_agents_md_points_only_to_the_learning_skill():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert LEARNING_SKILL in agents
    assert "setup-and-update" not in agents
    assert "e0 status" not in agents, "the session logic belongs to the skill, not to AGENTS.md"


def test_agents_md_is_short():
    """Students may edit AGENTS.md. The framework section must stay a short pointer."""
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert len(agents.splitlines()) <= 12
    assert len(agents) <= 800


def test_agents_md_has_do_not_modify_marker():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert "DO NOT MODIFY" in agents


def test_readme_tells_the_student_to_say_hi():
    readme = (TEMPLATE / "README.md").read_text(encoding="utf-8").lower()
    assert "hi" in readme


def _redirects_to_agents_md(path):
    if path.is_symlink():
        return path.resolve() == (TEMPLATE / "AGENTS.md").resolve()
    return "AGENTS.md" in path.read_text(encoding="utf-8")


def test_claude_md_redirects_to_agents_md():
    assert _redirects_to_agents_md(TEMPLATE / "CLAUDE.md")


def test_copilot_instructions_redirect_to_agents_md():
    assert _redirects_to_agents_md(TEMPLATE / ".github" / "copilot-instructions.md")
