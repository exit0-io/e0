"""The end of a task: review, comprehension questions, and their records on GitHub.

conversation (2026-09-26): the review follows the task's own rules and nothing else; the rules
never touch the disk. The questions are the canonical bank, personalized against the
student's diff. Both are recorded on GitHub, not locally.
"""

import hashlib
import json

import pytest

from conftest import CI_PASSING, DIFF_FILE, ISSUES_FILE, PRS_FILE


@pytest.fixture
def with_pr(run_e0, student_repo, write_task_file, set_issues, set_prs):
    run_e0(["init"], student_repo)
    write_task_file(student_repo, "T010")
    set_issues(student_repo, [("T010", "OPEN")])
    set_prs(student_repo, [("T010", "OPEN", {"statusCheckRollup": CI_PASSING})])
    return student_repo


# ---------------------------------------------------------------- e0 review


def test_review_hands_over_the_diff_and_the_rules_only(run_e0, with_pr):
    payload, code = run_e0(["review", "T010"], with_pr)
    assert code == 0 and "problem" not in payload, payload
    data = payload["data"]
    assert data["pr"]["number"] == 101
    assert "def greet(name)" in data["diff"]
    assert "Do not close a pull request before it has been reviewed" in data["rules"]["course"]
    assert "produced by a function" in data["rules"]["task"]
    assert "only" in payload["message"] and "e0 post-review T010" in payload["message"]


def test_the_rules_never_touch_the_disk(run_e0, with_pr):
    run_e0(["review", "T010"], with_pr)
    written = [p for p in with_pr.rglob("*") if p.is_file() and "rules" in p.name.lower()]
    assert written == []


def test_review_without_a_pull_request_says_the_student_opens_one(run_e0, with_pr, set_prs):
    set_prs(with_pr, [])
    payload, _ = run_e0(["review", "T010"], with_pr)
    assert "problem" in payload
    assert "no pull request" in payload["problem"]
    assert "opens a pull request" in payload["guidance"]


def test_review_waits_for_green_ci(run_e0, with_pr, set_prs):
    """eval 24 (2026-09-26): with CI red, haiku ran e0 review anyway. The fact that a review
    needs green checks lives in e0, so the agent gets a problem, not a diff."""
    from conftest import CI_FAILING, CI_PENDING

    for rollup, word in ((CI_FAILING, "failing"), (CI_PENDING, "pending")):
        set_prs(with_pr, [("T010", "OPEN", {"statusCheckRollup": rollup})])
        payload, _ = run_e0(["review", "T010"], with_pr)
        assert "problem" in payload, word
        assert word in payload["problem"]
        assert "CI is not green" in payload["guidance"]
        assert "diff" not in payload.get("data", {})

    set_prs(with_pr, [("T010", "OPEN")])  # no CI at all: the early tasks
    payload, _ = run_e0(["review", "T010"], with_pr)
    assert "problem" not in payload


def test_review_on_an_unstarted_task_is_a_problem(run_e0, with_pr):
    payload, _ = run_e0(["review", "T020"], with_pr)
    assert "problem" in payload


# ---------------------------------------------------------------- e0 post-review


def test_post_review_posts_a_marked_review_that_status_counts(run_e0, with_pr, tmp_path):
    review = tmp_path / "review.md"
    review.write_text("## Review of T010\n\nThe greeting is a function. Good.\n", encoding="utf-8")
    payload, code = run_e0(["post-review", "T010", str(review)], with_pr)
    assert code == 0 and "problem" not in payload, payload
    assert payload["data"]["pr"]["url"].endswith("/pull/101")
    assert "pull/101" in payload["message"]

    prs = json.loads((with_pr / PRS_FILE).read_text(encoding="utf-8"))
    body = prs[0]["reviews"][0]["body"]
    assert body.startswith("<!-- e0:review -->")
    assert "The greeting is a function" in body

    status, _ = run_e0(["status"], with_pr)
    assert status["data"]["inProgress"][0]["pr"]["reviews"] == 1

    run_e0(["post-review", "T010", str(review)], with_pr)
    status, _ = run_e0(["status"], with_pr)
    assert status["data"]["inProgress"][0]["pr"]["reviews"] == 2, "a second review is fine"


def test_post_review_needs_a_file_with_text(run_e0, with_pr, tmp_path):
    payload, _ = run_e0(["post-review", "T010"], with_pr)
    assert "problem" in payload and "<file>" in payload["guidance"]

    payload, _ = run_e0(["post-review", "T010", str(tmp_path / "missing.md")], with_pr)
    assert "problem" in payload and "does not exist" in payload["problem"]

    empty = tmp_path / "empty.md"
    empty.write_text("\n", encoding="utf-8")
    payload, _ = run_e0(["post-review", "T010", str(empty)], with_pr)
    assert "problem" in payload and "empty" in payload["problem"]


# ---------------------------------------------------------------- e0 questions


def test_questions_are_decoded_shuffled_and_come_with_the_diff(run_e0, with_pr):
    payload, code = run_e0(["questions", "T010"], with_pr)
    assert code == 0 and "problem" not in payload, payload
    data = payload["data"]
    by_id = {q["id"]: q for q in data["questions"]}
    # The task's own bank plus the related topic's bank.
    assert set(by_id) == {"c9f01a55", "d3b7c018", "b1d4e7a2"}

    mcq = by_id["c9f01a55"]
    assert mcq["answer"] == "None"
    assert sorted(mcq["options"]) == ["0", "An empty string", "It raises an error", "None"]
    assert "answerHash" not in mcq

    pipes = by_id["b1d4e7a2"]
    assert hashlib.sha256(pipes["answer"].encode()).hexdigest() == "146e5504f3ce8d105ed2f43846454c74978d8a34ee0137b954ced077365536b3"

    open_question = by_id["d3b7c018"]
    assert open_question["type"] == "open"
    assert "caller decide" in open_question["outline"]
    assert open_question["mandatory"] is True
    assert "answer" not in open_question

    assert "def greet(name)" in data["diff"]
    assert data["recorded"] is False
    assert "e0 record T010" in payload["message"]


def test_questions_shuffle_the_options(run_e0, with_pr):
    seen = set()
    for _ in range(12):
        payload, _ = run_e0(["questions", "T010"], with_pr)
        mcq = next(q for q in payload["data"]["questions"] if q["id"] == "c9f01a55")
        seen.add(tuple(mcq["options"]))
    assert len(seen) > 1, "the position of the answer must not teach anything"


def test_questions_work_without_github(run_e0, with_pr, gh_unavailable):
    gh_unavailable(with_pr)
    payload, _ = run_e0(["questions", "T010"], with_pr)
    assert "problem" not in payload
    assert len(payload["data"]["questions"]) == 3
    assert payload["data"]["diff"] is None


def test_questions_of_a_task_without_a_bank(run_e0, with_pr):
    payload, _ = run_e0(["questions", "T020"], with_pr)
    assert "problem" not in payload
    assert payload["data"]["questions"] == []
    assert "no questions" in payload["message"]


# ---------------------------------------------------------------- e0 record


def test_record_comments_on_the_issue_and_status_sees_it(run_e0, with_pr, set_issues, tmp_path):
    summary = tmp_path / "summary.md"
    summary.write_text("## Comprehension check\n\n- pipes: correct\n- return value: discussed\n", encoding="utf-8")
    payload, code = run_e0(["record", "T010", str(summary)], with_pr)
    assert code == 0 and "problem" not in payload, payload
    assert "issues/1#issuecomment-1" in payload["data"]["url"]

    issues = json.loads((with_pr / ISSUES_FILE).read_text(encoding="utf-8"))
    body = issues[0]["comments"][0]["body"]
    assert body.startswith("<!-- e0:questions -->")
    assert "pipes: correct" in body

    # The record survives the issue being closed: that is where status reads it.
    issues[0]["state"] = "CLOSED"
    (with_pr / ISSUES_FILE).write_text(json.dumps(issues), encoding="utf-8")
    status, _ = run_e0(["status"], with_pr)
    assert status["data"]["completed"][0]["questions"] == "done"
    questions, _ = run_e0(["questions", "T010"], with_pr)
    assert questions["data"]["recorded"] is True

    state = with_pr / ".exit0" / "state"
    assert [p.name for p in state.iterdir()] == ["profile.json"], "nothing recorded locally"


def test_record_on_a_task_without_an_issue_is_a_problem(run_e0, with_pr, tmp_path):
    summary = tmp_path / "summary.md"
    summary.write_text("skipped\n", encoding="utf-8")
    payload, _ = run_e0(["record", "T020", str(summary)], with_pr)
    assert "problem" in payload
    assert "no issue" in payload["problem"]


def test_the_diff_can_be_shaped_by_the_fixture(run_e0, with_pr):
    (with_pr / DIFF_FILE).write_text("diff --git a/init.sh b/init.sh\n+cat log | wc -l\n", encoding="utf-8")
    payload, _ = run_e0(["review", "T010"], with_pr)
    assert "cat log | wc -l" in payload["data"]["diff"]
