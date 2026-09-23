import json

import pytest

from conftest import _git


@pytest.fixture
def initialized(run_e0, student_repo):
    run_e0(["init"], student_repo)
    return student_repo


@pytest.fixture
def git():
    return _git


def test_status_on_a_fresh_course_lists_the_ready_tasks(run_e0, initialized):
    payload, code = run_e0(["status"], initialized)
    assert code == 0
    assert "problem" not in payload
    assert [task["id"] for task in payload["data"]["next"]] == ["T010"]
    assert payload["data"]["inProgress"] == []
    assert payload["data"]["completed"] == []


def test_progress_comes_from_github_issues(run_e0, initialized, set_issues):
    """An open issue titled [T010] ... is in progress. A closed one is complete."""
    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert [task["id"] for task in payload["data"]["inProgress"]] == ["T010"]
    assert payload["data"]["inProgress"][0]["issue"]["number"] == 1
    assert payload["data"]["next"] == []
    assert "T010" in payload["message"]

    set_issues(initialized, [("T010", "CLOSED")])
    payload, _ = run_e0(["status"], initialized)
    assert [t["id"] for t in payload["data"]["completed"]] == ["T010"]
    assert [task["id"] for task in payload["data"]["next"]] == ["T020"]


def test_status_next_is_a_list_because_tasks_form_a_tree(run_e0, initialized):
    payload, _ = run_e0(["status"], initialized)
    assert isinstance(payload["data"]["next"], list)
    assert "T020" not in [task["id"] for task in payload["data"]["next"]]


def test_an_open_issue_wins_over_a_closed_one_for_the_same_task(run_e0, initialized, set_issues):
    set_issues(initialized, [("T010", "CLOSED"), ("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert [task["id"] for task in payload["data"]["inProgress"]] == ["T010"]
    assert payload["data"]["completed"] == []


def test_issues_that_are_not_tasks_are_ignored(run_e0, initialized, set_issues):
    set_issues(
        initialized,
        [
            {"number": 7, "title": "Fix the README", "state": "OPEN", "url": "u"},
            {"number": 8, "title": "[T999] not a task", "state": "OPEN", "url": "u"},
            {"number": 9, "title": "[t010] lowercase is fine", "state": "OPEN", "url": "u"},
        ],
    )
    payload, _ = run_e0(["status"], initialized)
    assert [task["id"] for task in payload["data"]["inProgress"]] == ["T010"]


def test_status_message_links_the_issue_of_a_task_in_progress(run_e0, initialized, set_issues):
    """The agent copies the message; the student must be able to click through."""
    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert "https://github.com/student/repo/issues/1" in payload["message"]


def test_status_links_pull_requests_to_tasks(run_e0, initialized, set_issues, set_prs):
    set_issues(initialized, [("T010", "OPEN")])
    set_prs(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    pr = payload["data"]["inProgress"][0]["pr"]
    assert pr["number"] == 101
    assert pr["state"] == "OPEN"
    assert pr["merged"] is False


def test_a_pr_can_be_linked_by_mentioning_the_issue_number(run_e0, initialized, set_issues, set_prs):
    set_issues(initialized, [("T010", "CLOSED")])
    set_prs(
        initialized,
        [{"number": 5, "title": "greeting function", "state": "MERGED", "url": "u", "body": "Closes #1"}],
    )
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["completed"][0]["pr"]["merged"] is True
    assert payload["data"]["warnings"] == []


def test_a_closed_issue_without_a_merged_pr_is_flagged(run_e0, initialized, set_issues, set_prs):
    """The student may skip the PR. The agent must be told, so it can tell them."""
    set_issues(initialized, [("T010", "CLOSED")])
    payload, _ = run_e0(["status"], initialized)
    kinds = {(w["kind"], w["taskId"]) for w in payload["data"]["warnings"]}
    assert kinds == {("closed_without_pr", "T010")}
    assert "reopen" in payload["data"]["warnings"][0]["message"]

    set_prs(initialized, [("T010", "CLOSED")])  # closed, not merged: still flagged
    payload, _ = run_e0(["status"], initialized)
    assert len(payload["data"]["warnings"]) == 1

    set_prs(initialized, [("T010", "CLOSED"), ("T010", "MERGED")])
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["warnings"] == []
    assert payload["data"]["completed"][0]["pr"]["merged"] is True


def test_status_without_gh_is_a_problem_with_guidance(run_e0, initialized, gh_unavailable):
    gh_unavailable(initialized)
    payload, code = run_e0(["status"], initialized)
    assert code == 0
    assert "problem" in payload
    assert "gh auth" in payload["guidance"]


def test_status_carries_no_workflow_text(run_e0, initialized):
    """Procedure lives in the learning skill, not in the status envelope."""
    payload, _ = run_e0(["status"], initialized)
    assert "workflow" not in payload["data"]
    assert "contentTag" not in payload["data"]


def test_nothing_about_progress_is_stored_locally(run_e0, initialized, set_issues):
    set_issues(initialized, [("T010", "OPEN")])
    run_e0(["status"], initialized)
    state = initialized / ".exit0" / "state"
    assert [p.name for p in state.iterdir()] == ["profile.json"]


def test_available_tasks_needs_every_dependency_complete(e0mod, initialized):
    catalog = e0mod.read_catalog(initialized)
    assert [t["id"] for t in e0mod.available_tasks(catalog, {})] == ["T010"]
    assert [t["id"] for t in e0mod.available_tasks(catalog, {"T010": "in_progress"})] == []
    assert [t["id"] for t in e0mod.available_tasks(catalog, {"T010": "complete"})] == ["T020"]


def test_unmet_dependencies_lists_incomplete_prerequisites(e0mod, initialized):
    catalog = e0mod.read_catalog(initialized)
    task = e0mod.find_task(catalog, "T020")
    assert e0mod.unmet_dependencies(task, {}) == ["T010"]
    assert e0mod.unmet_dependencies(task, {"T010": "complete"}) == []


def test_status_always_reports_update_as_unknown(run_e0, initialized):
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["update"] == "unknown"


def test_bare_e0_runs_status(run_e0, initialized):
    payload, code = run_e0([], initialized)
    assert code == 0
    assert payload["command"] == "status"


def test_status_before_init_gives_guidance(run_e0, student_repo):
    payload, code = run_e0(["status"], student_repo)
    assert code == 0
    assert "problem" in payload
    assert "init" in payload["guidance"]


def test_status_reports_the_current_branch(run_e0, initialized, git):
    """conversation.md: the agent must know which branch the student is on, to catch work on
    main and misnamed branches. The fact comes from e0, never inferred."""
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["branch"] == "main"

    git(initialized, "checkout", "-q", "-b", "<task-branch>")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["branch"] == "<task-branch>"


def test_a_task_in_progress_on_main_is_flagged(run_e0, initialized, set_issues, git):
    """conversation.md: task work belongs on a task branch. Nothing in progress: no warning."""
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["warnings"] == []

    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    kinds = {(w["kind"], w["taskId"]) for w in payload["data"]["warnings"]}
    assert kinds == {("on_main", "T010")}
    # evals 07 and 12: a cheap model pasted all three branch commands at once. The warning
    # carries the first command and the pace, so there is nothing to infer.
    message = payload["data"]["warnings"][0]["message"]
    assert "git checkout main" in message
    assert "one command per message" in message
    assert ".exit0/skills/learning/references/git.md" in message

    git(initialized, "checkout", "-q", "-b", "t010-say-hello")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["warnings"] == []


def _add_origin(repo, tmp_path, git):
    remote = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "-u", "origin", "main")


def test_status_reports_the_working_tree(run_e0, initialized, git, tmp_path):
    """git.md comments (2026-09-23): the agent must know whether files were edited, committed
    on main, or caught in a conflict, without looking. e0 says."""
    payload, _ = run_e0(["status"], initialized)
    facts = payload["data"]["git"]
    assert facts["branch"] == "main"
    assert facts["uncommitted"] == [] and facts["conflicts"] == []
    assert facts["unpushedCommits"] is None, "no origin yet: e0 does not guess"

    _add_origin(initialized, tmp_path, git)
    (initialized / "greeting.py").write_text("print('hi')\n", encoding="utf-8")
    payload, _ = run_e0(["status"], initialized)
    facts = payload["data"]["git"]
    assert facts["uncommitted"] == ["greeting.py"]
    assert facts["unpushedCommits"] == 0

    git(initialized, "add", "greeting.py")
    git(initialized, "commit", "-q", "-m", "greet")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["git"]["uncommitted"] == []
    assert payload["data"]["git"]["unpushedCommits"] == 1


def test_status_reports_conflicted_files(run_e0, initialized, git):
    (initialized / "greeting.py").write_text("hello\n", encoding="utf-8")
    git(initialized, "add", "greeting.py")
    git(initialized, "commit", "-q", "-m", "hello")
    git(initialized, "checkout", "-q", "-b", "t010-say-hello", "HEAD~1")
    (initialized / "greeting.py").write_text("shalom\n", encoding="utf-8")
    git(initialized, "add", "greeting.py")
    git(initialized, "commit", "-q", "-m", "shalom")
    assert _git_merge_fails(initialized)

    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["git"]["conflicts"] == ["greeting.py"]
    assert payload["data"]["git"]["uncommitted"] == []


def _git_merge_fails(repo):
    import subprocess

    proc = subprocess.run(["git", "merge", "main"], cwd=str(repo), capture_output=True, text=True)
    return proc.returncode != 0


def test_on_main_warning_names_what_the_student_already_did(
    run_e0, initialized, set_issues, git, tmp_path
):
    """git.md comments (2026-09-23): the fix differs when nothing is edited, when files are
    edited but not committed, and when commits sit on main that GitHub does not have."""
    _add_origin(initialized, tmp_path, git)
    set_issues(initialized, [("T010", "OPEN")])

    def on_main():
        payload, _ = run_e0(["status"], initialized)
        return next(w for w in payload["data"]["warnings"] if w["kind"] == "on_main")

    assert on_main()["state"] == "clean"

    (initialized / "greeting.py").write_text("print('hi')\n", encoding="utf-8")
    warning = on_main()
    assert warning["state"] == "uncommitted"
    assert "Uncommitted work on main" in warning["message"]

    git(initialized, "add", "greeting.py")
    git(initialized, "commit", "-q", "-m", "greet")
    warning = on_main()
    assert warning["state"] == "committed"
    assert "1 commit" in warning["message"] and "Commits on main" in warning["message"]


def test_a_task_started_out_of_order_is_flagged_until_dismissed(
    run_e0, initialized, set_issues, e0mod
):
    """SKILL.md comment (2026-09-23): a student who starts from a later task hears which tasks
    they skipped. If they choose to ignore them, the reminder sleeps for some days."""
    set_issues(initialized, [("T020", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    warning = next(w for w in payload["data"]["warnings"] if w["kind"] == "dependency")
    assert warning["taskId"] == "T020" and warning["missing"] == ["T010"]
    assert "e0 dismiss T020" in warning["message"]

    payload, code = run_e0(["dismiss", "T020"], initialized)
    assert code == 0 and "problem" not in payload
    assert payload["data"]["taskId"] == "T020"
    payload, _ = run_e0(["status"], initialized)
    assert all(w["kind"] != "dependency" for w in payload["data"]["warnings"])

    import datetime

    later = datetime.date.today() + datetime.timedelta(days=e0mod.DISMISS_DAYS + 1)
    assert e0mod.read_dismissed(initialized, today=later) == {}, "a dismissal expires"
    payload, _ = run_e0(["dismiss"], initialized)
    assert "problem" in payload


def test_several_tasks_in_progress_on_main_ask_which_one_first(run_e0, initialized, set_issues):
    set_issues(initialized, [("T010", "OPEN"), ("T020", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    warning = next(w for w in payload["data"]["warnings"] if w["kind"] == "on_main")
    assert "T010, T020" in warning["message"]
    assert "ask which one" in warning["message"]


def test_a_branch_that_names_no_task_is_flagged_when_several_are_in_progress(
    run_e0, initialized, set_issues, git
):
    """git.md comment (2026-09-23): 'test123' with two open issues tells nobody which task
    the work is for. A branch that holds the task id or title is fine."""
    set_issues(initialized, [("T010", "OPEN"), ("T020", "OPEN")])
    git(initialized, "checkout", "-q", "-b", "test123")
    payload, _ = run_e0(["status"], initialized)
    kinds = {w["kind"] for w in payload["data"]["warnings"]}
    assert "unclear_branch" in kinds and "on_main" not in kinds
    assert payload["data"]["branchTask"] is None

    for name, task in (("t020-goodbye", "T020"), ("feature/say-hello", "T010")):
        git(initialized, "checkout", "-q", "-b", name)
        payload, _ = run_e0(["status"], initialized)
        assert payload["data"]["branchTask"] == task
        assert all(w["kind"] != "unclear_branch" for w in payload["data"]["warnings"])

    set_issues(initialized, [("T010", "OPEN")])
    git(initialized, "checkout", "-q", "test123")
    payload, _ = run_e0(["status"], initialized)
    assert all(w["kind"] != "unclear_branch" for w in payload["data"]["warnings"]), (
        "one task in progress: the branch can only be for it"
    )


def test_status_never_says_unlock(run_e0, initialized, set_issues):
    """conversation.md: tasks build on each other. This is the industry, not a game."""
    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert "unlock" not in json.dumps(payload).lower()


def test_status_when_all_tasks_complete(run_e0, initialized, set_issues):
    set_issues(initialized, [("T010", "CLOSED"), ("T020", "CLOSED")])
    payload, _ = run_e0(["status"], initialized)
    assert "problem" not in payload
    assert payload["data"]["inProgress"] == []
    assert payload["data"]["next"] == []
    assert payload["message"] == "Every task is complete."
