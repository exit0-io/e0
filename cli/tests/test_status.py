import json

import pytest

from conftest import _git, push_to_bare_origin


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
    assert [task["id"] for task in payload["data"]["ready"]] == ["T010"]
    assert payload["data"]["inProgress"] == []
    assert payload["data"]["completed"] == []
    assert payload["data"]["stand"]["kind"] == "nothing_in_progress"
    assert "T010" in payload["data"]["stand"]["message"]
    assert "Want to start one" in payload["data"]["stand"]["message"]


def test_progress_comes_from_github_issues(run_e0, initialized, set_issues):
    """An open issue titled [T010] ... is in progress. A closed one is complete."""
    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert [task["id"] for task in payload["data"]["inProgress"]] == ["T010"]
    assert payload["data"]["inProgress"][0]["issue"]["number"] == 1
    assert payload["data"]["ready"] == []
    assert payload["data"]["stand"]["kind"] == "on_main"

    set_issues(initialized, [("T010", "CLOSED")])
    payload, _ = run_e0(["status"], initialized)
    assert [t["id"] for t in payload["data"]["completed"]] == ["T010"]
    assert [task["id"] for task in payload["data"]["ready"]] == ["T020"]


def test_status_ready_is_a_list_because_tasks_form_a_tree(run_e0, initialized):
    payload, _ = run_e0(["status"], initialized)
    assert isinstance(payload["data"]["ready"], list)
    assert "T020" not in [task["id"] for task in payload["data"]["ready"]]


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
    assert payload["data"]["inProgress"][0]["issue"]["url"] == "https://github.com/student/repo/issues/1"


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
    message = payload["data"]["warnings"][0]["message"]
    # conversation (2026-10-07): the message is the exact text for the student.
    assert "gh issue reopen 1" in message
    assert "the student" not in message and "Tell them" not in message

    set_prs(initialized, [("T010", "CLOSED")])  # closed, not merged: still flagged
    payload, _ = run_e0(["status"], initialized)
    assert len(payload["data"]["warnings"]) == 1

    set_prs(initialized, [("T010", "CLOSED"), ("T010", "MERGED")])
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["warnings"] == []
    assert payload["data"]["completed"][0]["pr"]["merged"] is True


# 2026-10-07: e0 runs every gh command. When it cannot, it says why in a `kind` and in a
# message written for the student, as warnings do, and status fails hard: without GitHub the
# picture of progress would be wrong.


def test_status_when_gh_is_logged_out(run_e0, initialized, gh_unavailable):
    gh_unavailable(initialized)
    payload, code = run_e0(["status"], initialized)
    assert code == 0
    assert payload["kind"] == "gh_logged_out"
    assert "gh auth login" in payload["message"]
    assert "data.message" in payload["guidance"]
    assert "data" not in payload


def test_status_when_gh_is_missing_links_the_official_install_guide(run_e0, initialized):
    payload, _ = run_e0(["status"], initialized, gh=False)
    assert payload["kind"] == "gh_missing"
    assert "https://github.com/cli/cli#installation" in payload["message"]
    assert "gh auth login" in payload["message"]


def test_status_when_git_is_missing(run_e0, initialized):
    """The student text lives in e0, same as gh_missing. The agent sends data.message."""
    payload, code = run_e0(["status"], initialized, git=False)
    assert code == 0
    assert payload["kind"] == "git_missing"
    assert "https://git-scm.com/downloads" in payload["message"]
    assert "git --version" in payload["message"]
    assert "data.message" in payload["guidance"]
    assert "clone" not in payload["message"].lower()
    assert "data" not in payload


def test_status_outside_a_git_repo(run_e0, tmp_path):
    """Git is installed, but this folder is not a repo. A different student text; e0 still
    writes it, so the agent does not guess why status failed."""
    empty = tmp_path / "not-a-repo"
    empty.mkdir()
    payload, code = run_e0(["status"], empty)
    assert code == 0
    assert payload["kind"] == "not_a_git_repo"
    assert str(empty.resolve()) in payload["message"]
    assert "data.message" in payload["guidance"]
    assert "git-scm.com" not in payload["message"]
    assert "data" not in payload


def test_status_without_an_origin(run_e0, initialized, git):
    git(initialized, "remote", "remove", "origin")
    git(initialized, "remote", "add", "github", "https://github.com/student/repo.git")
    payload, _ = run_e0(["status"], initialized)
    assert payload["kind"] == "no_github_remote", "a GitHub remote not called origin does not count"
    assert "no remote called `origin`" in payload["message"]
    assert "git remote add origin" in payload["message"]


def test_status_with_an_origin_off_github(run_e0, initialized, git):
    git(initialized, "remote", "set-url", "origin", "https://gitlab.com/student/repo.git")
    payload, _ = run_e0(["status"], initialized)
    assert payload["kind"] == "no_github_remote"
    assert "https://gitlab.com/student/repo.git" in payload["message"]
    assert "git remote set-url origin" in payload["message"]


def test_status_when_gh_fails_for_another_reason(run_e0, initialized, gh_unavailable):
    gh_unavailable(initialized, error="error connecting to api.github.com", logged_in=True)
    payload, _ = run_e0(["status"], initialized)
    assert payload["kind"] == "gh_failed"
    assert "error connecting to api.github.com" in payload["message"]
    assert "https://github.com/exit0-io/e0/issues" in payload["message"]


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/student/repo.git",
        "https://github.com/student/repo",
        "git@github.com:student/repo.git",
        "ssh://git@github.com/student/repo.git",
        "https://token@github.com/student/repo/",
    ],
)
def test_origin_repo_reads_every_github_url_shape(e0mod, initialized, git, url):
    git(initialized, "remote", "set-url", "origin", url)
    assert e0mod.origin_repo(initialized) == "student/repo"


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


def test_bare_e0_runs_status(run_e0, initialized):
    payload, code = run_e0([], initialized)
    assert code == 0
    assert payload["command"] == "status"


def test_status_before_init_gives_guidance(run_e0, student_repo):
    payload, code = run_e0(["status"], student_repo)
    assert code == 0
    assert "problem" in payload
    assert "init" in payload["guidance"]


def test_status_reports_the_current_branch_once(run_e0, initialized, git):
    """conversation.md: the agent must know which branch the student is on, to catch work on
    main and misnamed branches. The fact comes from e0, never inferred, and lives in one
    place: status.git (conversation, 2026-09-24: 'you must think simplicity')."""
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["git"]["branch"] == "main"
    assert "branch" not in payload["data"] and "branchTask" not in payload["data"]

    git(initialized, "checkout", "-q", "-b", "<task-branch>")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["git"]["branch"] == "<task-branch>"
    assert payload["data"]["stand"]["kind"] != "branch_brackets", "no task in progress yet"


def test_work_on_main_is_a_git_fact_not_a_warning(run_e0, initialized, set_issues, git):
    """conversation (2026-09-24): the on_main warning said the same thing as the git.md
    template, so the student heard it twice, and its taskId could not name several open
    tasks. status.git carries the facts; git.md maps them to one message."""
    set_issues(initialized, [("T010", "OPEN"), ("T020", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert {w["kind"] for w in payload["data"]["warnings"]} <= {"dependency"}
    assert payload["data"]["git"]["branch"] == "main"
    assert payload["data"]["git"]["task"] is None
    assert payload["data"]["stand"]["kind"] == "on_main"
    assert "never work on it directly" in payload["data"]["stand"]["message"]

    git(initialized, "checkout", "-q", "-b", "t010-say-hello")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["git"]["task"] == "T010"
    assert payload["data"]["stand"]["kind"] == "start_working"
    assert "Want to start working on it?" in payload["data"]["stand"]["message"]


def _add_origin(repo, tmp_path, git):
    push_to_bare_origin(repo, tmp_path / "origin.git")


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
    """A merge conflict is a problem: the student text is the message, guidance starts the
    simulator. Nothing else until they fix it."""
    (initialized / "greeting.py").write_text("hello\n", encoding="utf-8")
    git(initialized, "add", "greeting.py")
    git(initialized, "commit", "-q", "-m", "hello")
    git(initialized, "checkout", "-q", "-b", "t010-say-hello", "HEAD~1")
    (initialized / "greeting.py").write_text("shalom\n", encoding="utf-8")
    git(initialized, "add", "greeting.py")
    git(initialized, "commit", "-q", "-m", "shalom")
    assert _git_merge_fails(initialized)

    payload, code = run_e0(["status"], initialized)
    assert code == 0
    assert payload["kind"] == "merge_conflict"
    assert "data" not in payload
    assert "greeting.py" in payload["message"]
    assert "t010-say-hello" in payload["message"] and "`main`" in payload["message"]
    assert "<<<<<<<" in payload["message"] and "Merge Editor" in payload["message"]
    assert "conflict.html?" in payload["message"] and "localhost:8765" in payload["message"]
    assert "http.server 8765" in payload["guidance"]
    assert "data.message" in payload["guidance"]


def test_merging_from_is_null_outside_a_merge(run_e0, initialized):
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["git"]["mergingFrom"] is None


def _git_merge_fails(repo):
    import subprocess

    proc = subprocess.run(["git", "merge", "main"], cwd=str(repo), capture_output=True, text=True)
    return proc.returncode != 0


def test_a_task_started_out_of_order_is_flagged_until_dismissed(
    run_e0, initialized, set_issues, e0mod
):
    """SKILL.md comment (2026-09-23): a student who starts from a later task hears which tasks
    they skipped. If they choose to ignore them, the reminder sleeps for some days."""
    set_issues(initialized, [("T020", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    warning = next(w for w in payload["data"]["warnings"] if w["kind"] == "dependency")
    assert warning["taskId"] == "T020" and warning["missing"] == ["T010"]
    # conversation (2026-10-07): the message is for the student; `missing` is for the agent,
    # and `e0 dismiss` is the agent's move, named in the skill, not in what the student reads.
    assert "T020 builds on T010" in warning["message"]
    assert "skip" in warning["message"] and str(e0mod.DISMISS_DAYS) in warning["message"]
    assert "e0 dismiss" not in warning["message"] and "the student" not in warning["message"]

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


def test_git_task_says_which_task_in_progress_the_branch_is_for(
    run_e0, initialized, set_issues, git
):
    """git.md comment (2026-09-23): 'test123' with two open issues tells nobody which task
    the work is for. A branch that holds the task id or title does. The fact is
    status.git.task; the question to the student is git.md's."""
    set_issues(initialized, [("T010", "OPEN"), ("T020", "OPEN")])
    git(initialized, "checkout", "-q", "-b", "test123")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["git"]["task"] is None
    assert payload["data"]["stand"]["kind"] == "unclear_branch"
    assert "test123" in payload["data"]["stand"]["message"]
    assert {w["kind"] for w in payload["data"]["warnings"]} <= {"dependency"}

    for name, task in (("t020-goodbye", "T020"), ("feature/say-hello", "T010")):
        git(initialized, "checkout", "-q", "-b", name)
        payload, _ = run_e0(["status"], initialized)
        assert payload["data"]["git"]["task"] == task

    set_issues(initialized, [("T010", "CLOSED")])
    git(initialized, "checkout", "-q", "feature/say-hello")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["git"]["task"] is None, "only tasks in progress count"


def test_status_never_says_unlock(run_e0, initialized, set_issues):
    """conversation.md: tasks build on each other. This is the industry, not a game."""
    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert "unlock" not in json.dumps(payload).lower()


# ---------------------------------------------------------------- the working part of a task
# conversation (2026-09-26): the agent must know, without inferring, whether the student has
# started on the branch, whether the tests passed, where the PR stands, and whether the
# questions were asked.


def test_status_counts_the_commits_on_the_task_branch(run_e0, initialized, git):
    """'start' when the branch is fresh, 'keep working' when it holds commits or edits."""
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["git"]["branchCommits"] == 0, "main is the baseline"

    git(initialized, "checkout", "-q", "-b", "t010-say-hello")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["git"]["branchCommits"] == 0

    (initialized / "greeting.py").write_text("x\n", encoding="utf-8")
    git(initialized, "add", "greeting.py")
    git(initialized, "commit", "-q", "-m", "greet")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["git"]["branchCommits"] == 1


def test_status_stand_on_the_task_branch(run_e0, initialized, set_issues, git):
    """Naming and start/keep are status facts. Checkout aborted and 'I finished' stay in the skill."""
    set_issues(initialized, [("T010", "OPEN")])
    git(initialized, "checkout", "-q", "-b", "<task-branch>")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["stand"]["kind"] == "branch_brackets"
    assert "git branch -m" in payload["data"]["stand"]["message"]

    git(initialized, "checkout", "-q", "-B", "test123")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["stand"]["kind"] == "branch_unnamed"
    assert "says nothing about the task" in payload["data"]["stand"]["message"]

    git(initialized, "checkout", "-q", "-B", "t010-say-hello")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["stand"]["kind"] == "start_working"
    assert "Want to start working on it?" in payload["data"]["stand"]["message"]

    (initialized / "greeting.py").write_text("x\n", encoding="utf-8")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["stand"]["kind"] == "keep_working"
    assert "greeting.py" in payload["data"]["stand"]["message"]


def test_status_stand_push_when_the_tests_passed(
    run_e0, initialized, set_issues, git, write_task_file
):
    """The push is a status fact: last run passed, no pull request, e0 fills the branch."""
    set_issues(initialized, [("T010", "OPEN")])
    git(initialized, "checkout", "-q", "-b", "t010-say-hello")
    write_task_file(initialized, "T010")
    checks = initialized / "tests" / "school-checks" / "t010"
    checks.mkdir(parents=True, exist_ok=True)
    (checks / "results.json").write_text(
        json.dumps({"passing": True, "passed": 1, "failed": 0, "failedTests": []}),
        encoding="utf-8",
    )
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["stand"]["kind"] == "push_branch"
    assert "git push -u origin t010-say-hello" in payload["data"]["stand"]["message"]
    assert "twin" in payload["data"]["stand"]["message"]

    (initialized / "extra.py").write_text("x\n", encoding="utf-8")
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["stand"]["kind"] == "push_branch"
    assert "extra.py" in payload["data"]["stand"]["message"]
    assert "git add extra.py" in payload["data"]["stand"]["message"]


def test_status_lists_local_branches_with_their_tasks(run_e0, initialized, set_issues, git):
    """conversation (2026-09-26): on main with an open issue, the agent suggests the branch the
    student already made for that task, if there is one, instead of a new one."""
    set_issues(initialized, [("T010", "OPEN")])
    git(initialized, "branch", "t010-say-hello")
    git(initialized, "branch", "scratch")
    payload, _ = run_e0(["status"], initialized)
    branches = {b["name"]: b["task"] for b in payload["data"]["git"]["branches"]}
    assert branches == {"main": None, "t010-say-hello": "T010", "scratch": None}
    assert payload["data"]["stand"]["kind"] == "on_main"
    assert "t010-say-hello" in payload["data"]["stand"]["message"]
    assert "already have a branch" in payload["data"]["stand"]["message"]


def test_status_reports_the_tests_of_a_task_in_progress(run_e0, initialized, set_issues, write_task_file):
    """The catalog says whether a task has checks; e0 says the command and the last run."""
    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    checks = payload["data"]["inProgress"][0]["checks"]
    assert checks == {"command": None, "lastRun": None}, "not downloaded yet: e0 does not guess"

    write_task_file(initialized, "T010")
    payload, _ = run_e0(["status"], initialized)
    checks = payload["data"]["inProgress"][0]["checks"]
    assert checks["command"] == "python3 -m pytest tests/school-checks/t010 -v"
    assert checks["lastRun"] is None


def test_a_task_without_checks_says_so(run_e0, initialized, set_issues, make_course_dir, content_server):
    payload, _ = run_e0(["status"], initialized)  # sanity: the fixture course has checks
    import json as _json

    catalog_path = initialized / ".exit0" / "catalog.json"
    catalog = _json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["tasks"][0]["checks"] = False
    catalog["tasks"][0]["questions"] = False
    catalog_path.write_text(_json.dumps(catalog), encoding="utf-8")

    set_issues(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["inProgress"][0]["checks"] is None

    set_issues(initialized, [("T010", "CLOSED")])
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["completed"][0]["questions"] is None


def test_status_reports_the_pull_request_ci_and_reviews(run_e0, initialized, set_issues, set_prs):
    from conftest import CI_FAILING, CI_PASSING, CI_PENDING

    set_issues(initialized, [("T010", "OPEN")])
    set_prs(initialized, [("T010", "OPEN")])
    payload, _ = run_e0(["status"], initialized)
    pr = payload["data"]["inProgress"][0]["pr"]
    assert pr["checks"] == "none" and pr["reviews"] == 0
    assert pr["branch"] == "t010-my-solution"
    assert payload["data"]["stand"]["kind"] == "review"
    assert "e0 review T010" in payload["data"]["stand"]["guidance"]

    set_prs(initialized, [("T010", "OPEN", {"statusCheckRollup": CI_PENDING})])
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["inProgress"][0]["pr"]["checks"] == "pending"
    assert payload["data"]["stand"]["kind"] == "ci_not_green"
    assert "still running" in payload["data"]["stand"]["message"]

    set_prs(initialized, [("T010", "OPEN", {"statusCheckRollup": CI_FAILING})])
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["inProgress"][0]["pr"]["checks"] == "failing"
    assert payload["data"]["stand"]["kind"] == "ci_not_green"
    assert "checks are red" in payload["data"]["stand"]["message"]
    assert "before you run or fix anything" in payload["data"]["stand"]["guidance"]

    set_prs(initialized, [("T010", "OPEN", {"statusCheckRollup": CI_PASSING})])
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["inProgress"][0]["pr"]["checks"] == "passing"
    assert payload["data"]["stand"]["kind"] == "review"

    reviews = [{"body": "looks fine", "state": "COMMENTED"}, {"body": "<!-- e0:review -->\n## Review", "state": "COMMENTED"}]
    set_prs(initialized, [("T010", "OPEN", {"statusCheckRollup": CI_PASSING, "reviews": reviews})])
    payload, _ = run_e0(["status"], initialized)
    pr = payload["data"]["inProgress"][0]["pr"]
    assert pr["reviews"] == 1, "only Exit0 reviews count"
    assert payload["data"]["stand"]["kind"] == "after_the_review"
    assert "Merge pull request" in payload["data"]["stand"]["message"]

    set_prs(initialized, [("T010", "MERGED")])
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["stand"]["kind"] == "close_the_issue"
    assert "gh issue close" in payload["data"]["stand"]["message"]


def test_ci_verdict_reads_both_rollup_shapes(e0mod):
    assert e0mod.ci_verdict([]) == "none"
    assert e0mod.ci_verdict(None) == "none"
    assert e0mod.ci_verdict([{"__typename": "StatusContext", "state": "SUCCESS"}]) == "passing"
    assert e0mod.ci_verdict([{"__typename": "StatusContext", "state": "PENDING"}]) == "pending"
    assert e0mod.ci_verdict([{"__typename": "CheckRun", "status": "QUEUED", "conclusion": None}]) == "pending"
    assert e0mod.ci_verdict([{"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "SKIPPED"}]) == "passing"
    assert e0mod.ci_verdict([
        {"__typename": "CheckRun", "status": "IN_PROGRESS", "conclusion": None},
        {"__typename": "CheckRun", "status": "COMPLETED", "conclusion": "FAILURE"},
    ]) == "failing", "one failure decides, whatever else is still running"


def test_status_reports_whether_the_questions_were_recorded(run_e0, initialized, set_issues):
    """The record is a marked comment on the issue: nothing local, readable from any clone."""
    set_issues(initialized, [("T010", "CLOSED")])
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["completed"][0]["questions"] == "pending"

    set_issues(
        initialized,
        [{"number": 1, "title": "[T010] Say hello", "state": "CLOSED", "url": "u",
          "comments": [{"body": "nice"}, {"body": "<!-- e0:questions -->\n2 of 3 correct"}]}],
    )
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["completed"][0]["questions"] == "done"


def test_status_message_leads_with_pending_questions(run_e0, initialized, set_issues, set_prs):
    """conversation (2026-10-07): T010 merged and closed, T020 open. The stand is the questions,
    not T020, so a cheap model does not skip them."""
    set_issues(initialized, [("T010", "CLOSED"), ("T020", "OPEN")])
    set_prs(initialized, [("T010", "MERGED")])
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["stand"]["kind"] == "questions_pending"
    assert "T010" in payload["data"]["stand"]["message"]
    assert "T020" not in payload["data"]["stand"]["message"]
    assert "e0 questions T010" in payload["data"]["stand"]["guidance"]

    set_prs(initialized, [])
    payload, _ = run_e0(["status"], initialized)
    assert payload["message"].startswith("Send the 1 warning(s) in data.warnings first")
    assert payload["data"]["stand"]["kind"] == "questions_pending"

    set_issues(
        initialized,
        [{"number": 1, "title": "[T010] Say hello", "state": "CLOSED", "url": "u",
          "comments": [{"body": "<!-- e0:questions -->\n2 of 3 correct"}]},
         ("T020", "OPEN")],
    )
    payload, _ = run_e0(["status"], initialized)
    assert payload["data"]["stand"]["kind"] != "questions_pending"


def test_status_when_all_tasks_complete(run_e0, initialized, set_issues):
    set_issues(initialized, [("T010", "CLOSED"), ("T020", "CLOSED")])
    payload, _ = run_e0(["status"], initialized)
    assert "problem" not in payload
    assert payload["data"]["inProgress"] == []
    assert payload["data"]["ready"] == []
    assert payload["message"].startswith("Send the 2 warning(s) in data.warnings first")
    assert payload["data"]["stand"]["kind"] == "questions_pending"
    assert "T010" in payload["data"]["stand"]["message"]
