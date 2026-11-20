"""A newer compatible e0 is a note on the JSON. The student runs the command."""

import json
import urllib.request

import pytest


@pytest.fixture
def checking(monkeypatch):
    """These tests are the ones that ask GitHub (through a fake)."""
    monkeypatch.delenv("E0_SKIP_UPGRADE_CHECK", raising=False)


def test_version_parts_reads_major_minor_and_patch(e0mod):
    assert e0mod.version_parts("v1.3") == (1, 3, 0)
    assert e0mod.version_parts("v1.3.1") == (1, 3, 1)
    assert e0mod.version_parts("v2") == (2, 0, 0)
    assert e0mod.version_parts("latest") is None
    assert e0mod.version_parts("v1.4-rc1") is None


def test_newer_compatible_is_a_later_release_of_the_same_major(e0mod):
    assert e0mod.newer_compatible("v1.3", "v1.4")
    assert e0mod.newer_compatible("v1.3", "v1.3.1")
    assert e0mod.newer_compatible("v1.3", "v1.10")
    assert not e0mod.newer_compatible("v1.3", "v1.3")
    assert not e0mod.newer_compatible("v1.3", "v1.2")
    assert not e0mod.newer_compatible("v1.3", "v2.0")
    assert not e0mod.newer_compatible("v1.3", "nope")


def test_latest_release_tag_reads_the_github_payload(e0mod, monkeypatch):
    class Body:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"tag_name": "v1.8"}'

    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: Body())
    assert e0mod.latest_release_tag() == "v1.8"


def test_latest_release_tag_is_none_when_github_is_unreachable(e0mod, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    assert e0mod.latest_release_tag() is None


def test_upgrade_note_uses_the_latest_url_and_names_no_tag(e0mod, student_repo, checking, monkeypatch):
    monkeypatch.setattr(e0mod, "latest_release_tag", lambda: "v1.4")
    message = e0mod.upgrade_message(student_repo)
    command = message.split("```")[1]
    assert "v1.4" in message and e0mod.E0_VERSION in message
    assert "releases/latest/download/e0" in command
    assert "v1.4" not in command and e0mod.E0_VERSION not in command
    assert "chmod +x .exit0/e0" in command and ".exit0/e0 init" in command
    assert "start a new chat" in message


def test_upgrade_note_on_windows_uses_curl_exe(e0mod, student_repo, checking, monkeypatch):
    monkeypatch.setattr(e0mod, "latest_release_tag", lambda: "v1.4")
    monkeypatch.setattr(e0mod, "detect_profile", lambda root: {"os": "windows"})
    command = e0mod.upgrade_message(student_repo).split("```")[1]
    assert 'curl.exe -fsSL "https://github.com/exit0-io/e0/releases/latest/download/e0"' in command
    assert "python .exit0/e0 init" in command
    assert "chmod" not in command


def test_no_note_when_latest_is_current_older_or_a_new_major(e0mod, student_repo, checking, monkeypatch):
    for tag in (e0mod.E0_VERSION, "v1.0", "v2.0", None):
        monkeypatch.setattr(e0mod, "latest_release_tag", lambda tag=tag: tag)
        assert e0mod.upgrade_message(student_repo) == ""


def test_every_reply_asks_github_again(e0mod, student_repo, checking, monkeypatch):
    """Saying the note once is the agent's job. e0 does not remember that it already checked."""
    calls = {"n": 0}

    def fetch():
        calls["n"] += 1
        return "v1.4"

    monkeypatch.setattr(e0mod, "latest_release_tag", fetch)
    first = e0mod.upgrade_message(student_repo)
    second = e0mod.upgrade_message(student_repo)
    assert first == second and "v1.4" in first
    assert calls["n"] == 2


def test_skip_env_does_not_ask_github(e0mod, student_repo, monkeypatch):
    def boom():
        raise AssertionError("should not ask GitHub")

    monkeypatch.setenv("E0_SKIP_UPGRADE_CHECK", "1")
    monkeypatch.setattr(e0mod, "latest_release_tag", boom)
    assert e0mod.upgrade_message(student_repo) == ""


def test_the_first_e0_of_a_run_carries_the_note(e0mod, student_repo, checking, monkeypatch, capsys):
    monkeypatch.chdir(student_repo)
    monkeypatch.setattr(e0mod, "latest_release_tag", lambda: "v1.4")
    assert e0mod.main(["help"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "help"
    assert "releases/latest/download/e0" in payload["upgrade"]
    assert "v1.4" not in payload["upgrade"].split("```")[1]
