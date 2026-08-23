import json
import pathlib

TEMPLATE = pathlib.Path(__file__).resolve().parents[2] / "courses" / "demo" / "template"


def test_template_has_required_files():
    for name in ("README.md", "AGENTS.md", "CLAUDE.md", ".exit0/config.json", ".gitignore"):
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
    for entry in ("content/", "tests/school-checks/", ".exit0/catalog.json", ".exit0/skills/"):
        assert entry in text, f".gitignore missing: {entry}"


def test_agents_md_has_curl_bootstrap():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert "curl" in agents
    assert "RELEASE" in agents
    assert ".exit0/e0 init" in agents


def test_agents_md_points_to_session_skill():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert "session.md" in agents


def test_agents_md_has_do_not_modify_marker():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert "DO NOT MODIFY" in agents


def test_readme_tells_the_student_to_say_hi():
    readme = (TEMPLATE / "README.md").read_text(encoding="utf-8").lower()
    assert "hi" in readme


def test_claude_md_redirects_to_agents_md():
    claude = (TEMPLATE / "CLAUDE.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in claude

