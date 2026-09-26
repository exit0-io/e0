import hashlib
import json
import pathlib

FIXTURE_COURSE = pathlib.Path(__file__).resolve().parent.parent.parent / "courses" / "demo" / "content"


def test_no_placeholder_hashes_remain():
    """Every answerHash and check file hash must be a real sha256."""
    offenders = []
    for path in FIXTURE_COURSE.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        if "REPLACED_IN_STEP_7" in text:
            offenders.append(str(path.relative_to(FIXTURE_COURSE)))
    assert offenders == [], f"placeholder hashes left in: {offenders}"


def test_answer_hashes_match_exactly_one_option():
    for path in FIXTURE_COURSE.rglob("questions.json"):
        bank = json.loads(path.read_text(encoding="utf-8"))
        for question in bank["questions"]:
            if question["type"] != "mcq":
                continue
            matches = [
                option
                for option in question["options"]
                if hashlib.sha256(option.encode("utf-8")).hexdigest()
                == question["answerHash"]
            ]
            assert len(matches) == 1, (
                f"{path.name} question {question['id']} must have exactly one "
                f"correct option, found {len(matches)}"
            )


def test_check_file_hashes_match_the_files_on_disk():
    for checks_json in FIXTURE_COURSE.rglob("checks/checks.json"):
        spec = json.loads(checks_json.read_text(encoding="utf-8"))
        for name, expected in spec["files"].items():
            actual = hashlib.sha256(
                (checks_json.parent / name).read_bytes()
            ).hexdigest()
            assert actual == expected, f"{name} hash is stale"


def test_every_dependson_and_relatedtopic_resolves():
    catalog = json.loads((FIXTURE_COURSE / "catalog.json").read_text(encoding="utf-8"))
    index = json.loads(
        (FIXTURE_COURSE / "knowledgebase" / "index.json").read_text(encoding="utf-8")
    )
    task_ids = {task["id"] for task in catalog["tasks"]}
    topic_ids = {topic["id"] for topic in index["topics"]}

    for task in catalog["tasks"]:
        for dependency in task["dependsOn"]:
            assert dependency in task_ids, f"{task['id']} depends on unknown {dependency}"
        for topic in task["relatedTopics"]:
            assert topic in topic_ids, f"{task['id']} references unknown topic {topic}"


def test_the_catalog_says_which_tasks_have_checks_and_questions():
    """conversation (2026-09-26): e0 learns from the catalog whether a task has tests and
    questions. The flag and the files must agree."""
    catalog = json.loads((FIXTURE_COURSE / "catalog.json").read_text(encoding="utf-8"))
    for task in catalog["tasks"]:
        folder = FIXTURE_COURSE / "tasks" / task["id"].lower()
        assert "checks" in task and "questions" in task, f"{task['id']} lacks the flags"
        assert task["checks"] == (folder / "checks" / "checks.json").exists(), task["id"]
        has_bank = (folder / "questions.json").exists() or any(
            (FIXTURE_COURSE / "knowledgebase" / topic / "questions.json").exists()
            for topic in task["relatedTopics"]
        )
        assert task["questions"] == has_bank, task["id"]


def test_the_pull_requests_topic_exists():
    """The skill links content/knowledge-base/pull-requests.md when it asks for a PR."""
    index = json.loads((FIXTURE_COURSE / "knowledgebase" / "index.json").read_text(encoding="utf-8"))
    assert "pull-requests" in {topic["id"] for topic in index["topics"]}
    assert (FIXTURE_COURSE / "knowledgebase" / "pull-requests" / "tutorial.md").exists()


def test_catalog_has_course_id_and_title():
    """Catalog must identify the course."""
    catalog = json.loads((FIXTURE_COURSE / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["course"]["id"]
    assert catalog["course"]["title"]
