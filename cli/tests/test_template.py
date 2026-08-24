import json
import pathlib

TEMPLATE = pathlib.Path(__file__).resolve().parents[2] / "courses" / "demo" / "template"


def test_template_has_required_files():
    for name in ("README.md", "AGENTS.md", "CLAUDE.md", ".exit0/config.json", ".exit0/README.md", ".gitignore"):
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


def test_exit0_readme_has_curl_bootstrap():
    readme = (TEMPLATE / ".exit0" / "README.md").read_text(encoding="utf-8")
    assert "curl" in readme
    assert "RELEASE" in readme
    assert ".exit0/e0 init" in readme


def test_agents_md_has_curl_bootstrap():
    # AGENTS.md points to .exit0/README.md; the curl command lives there
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert ".exit0/README.md" in agents


def test_agents_md_tells_agent_to_use_e0_status():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert "e0 status" in agents


def test_agents_md_has_do_not_modify_marker():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert "DO NOT MODIFY" in agents


def test_readme_tells_the_student_to_say_hi():
    readme = (TEMPLATE / "README.md").read_text(encoding="utf-8").lower()
    assert "hi" in readme


def test_claude_md_redirects_to_agents_md():
    claude = (TEMPLATE / "CLAUDE.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in claude

