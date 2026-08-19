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


def test_every_task_directory_has_checks():
    catalog = json.loads((FIXTURE_COURSE / "catalog.json").read_text(encoding="utf-8"))
    for task in catalog["tasks"]:
        checks = FIXTURE_COURSE / "tasks" / task["id"].lower() / "checks" / "checks.json"
        assert checks.exists(), f"{task['id']} has no checks.json"


def test_catalog_declares_its_framework_requirement():
    """e0 is released on its own cadence, so a course must state the minimum it needs."""
    catalog = json.loads((FIXTURE_COURSE / "catalog.json").read_text(encoding="utf-8"))
    assert "requiresE0" in catalog
    assert catalog["course"]["id"]
    assert catalog["course"]["title"]
