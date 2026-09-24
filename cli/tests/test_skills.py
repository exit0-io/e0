import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILLS = ROOT / "cli" / "skills"
E0_PATH = ROOT / "cli" / "bin" / "e0"

# The learning skill is the single entry point. Everything else is a reference inside it.
EXPECTED = {"learning"}
SETUP_REFERENCE = SKILLS / "learning" / "references" / "setup-and-update.md"
GIT_REFERENCE = SKILLS / "learning" / "references" / "git.md"

# Courses hosted by e0. None of these may appear in the CLI or in a framework skill.
COURSE_NAMES = ("polybot", "yoloservice", "mit2026", "polyaidev", "demo course")


def skill_files():
    return (
        list(SKILLS.glob("*/SKILL.md"))
        + list(SKILLS.glob("*/references/*.md"))
        + list(SKILLS.glob("*/assets/*"))
    )


def test_every_expected_skill_exists():
    present = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
    assert present == EXPECTED


def test_every_framework_skill_file_e0_downloads_exists(e0mod):
    for name, files in e0mod.FRAMEWORK_SKILLS.items():
        for relative in files:
            assert (SKILLS / name / relative).exists(), f"missing {name}/{relative}"


def test_e0_downloads_every_skill_file_that_exists(e0mod):
    """A skill file that e0 does not know about would never reach the student."""
    for path in skill_files():
        name = path.relative_to(SKILLS).parts[0]
        relative = path.relative_to(SKILLS / name).as_posix()
        assert relative in e0mod.FRAMEWORK_SKILLS.get(name, []), f"e0 does not download {name}/{relative}"


def test_skills_only_reference_real_commands():
    source = E0_PATH.read_text(encoding="utf-8")
    registered = set(re.findall(r'^\s{4}"([a-z-]+)": cmd_', source, re.MULTILINE))
    for path in skill_files():
        mentioned = set(re.findall(r"`e0 ([a-z-]+)", path.read_text(encoding="utf-8")))
        assert mentioned <= registered, f"{path} references unknown: {mentioned - registered}"


def test_the_framework_names_no_course():
    """One e0 serves every course, so it must not hardcode any of them."""
    targets = [E0_PATH, *skill_files()]
    for path in targets:
        text = path.read_text(encoding="utf-8").lower()
        for name in COURSE_NAMES:
            assert name not in text, f"{path} names the course '{name}'"


def test_learning_skill_checks_for_e0_before_running_status():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert ".exit0/e0" in text
    assert "references/setup-and-update.md" in text
    assert text.index("references/setup-and-update.md") < text.index("e0 status")


def test_learning_skill_has_the_agent_personalize_silently():
    """The spec's personalization contract, done by the agent, never narrated to the student."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "data.canonical" in text
    assert "data.personalization" in text and "variants" in text
    assert "retone" in text
    assert "hears nothing about it" in text
    assert "Every other character stays as it is" in text
    assert text.index("e0 task <id>") < text.index("e0 start <id>") < text.index("e0 verify <id>")


def test_learning_skill_reads_progress_from_github_issues():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "open issue" in text.lower()
    assert "gh auth login" in text


def test_setup_reference_has_the_bootstrap_and_points_back():
    text = SETUP_REFERENCE.read_text(encoding="utf-8")
    assert "curl" in text
    assert ".exit0/e0 init" in text
    assert "learning" in text


def test_setup_reference_mentions_the_cheap_model():
    text = SETUP_REFERENCE.read_text(encoding="utf-8").lower()
    assert "cheap" in text or "cheapest" in text


def test_setup_reference_falls_back_to_the_latest_release():
    """A pinned tag that was never published must not stop a student. Latest is the net."""
    text = SETUP_REFERENCE.read_text(encoding="utf-8")
    assert "releases/latest/download/e0" in text
    assert text.count("releases/latest/download/e0") >= 2, "bash and PowerShell both need it"


def test_setup_reference_names_curl_as_the_only_source_and_the_way_out():
    """A cheap model once told the student to `pip install exit0`. There is no such package."""
    text = SETUP_REFERENCE.read_text(encoding="utf-8")
    assert "comes only from the `curl` commands" in text
    assert "not a pip package" in text
    assert "https://github.com/exit0-io/e0/issues" in text
    skill = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "get it only by following [First-time setup]" in skill


def test_learning_skill_separates_looking_at_a_task_from_starting_it():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "e0 task" in text
    assert text.index("e0 task") < text.index("e0 start <id>")
    assert "preview" in text.lower(), "students must be told how to read Markdown"
    assert "](content/" in text, "file links must be clickable"


def test_learning_skill_names_the_protocol_and_its_shortcuts():
    """From conversation.md: the agent must know the road (issue, branch, PR, merge, close,
    questions) and say so when a closed issue has no merged PR."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "## The protocol" in text
    for step in ("Issue", "Branch", "Implement", "Pull request", "close the issue", "Comprehension"):
        assert step in text, f"protocol step missing: {step}"
    assert "closed_without_pr" in text
    assert "reopen" in text


def test_learning_skill_sends_the_student_to_a_branch_first():
    """From conversation.md: after handing over the task, the first move is a feature branch
    from an updated main, run by the student."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "git checkout -b" in text
    assert "git pull" in text
    assert "first move" in text


def test_learning_skill_sends_git_help_to_the_git_reference():
    """conversation.md: first task, a Git question, or work on main all lead to git.md, and the
    skill itself stays short."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "references/git.md" in text
    assert "status.branch" in text
    assert "on_main" in text
    assert "first task" in text.lower()


def test_git_reference_teaches_one_command_at_a_time():
    """conversation.md: explain, give one command, let the student run it, check, then the next.
    The placeholder mistake (a branch literally named <task-branch>) is called out and fixed."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    assert "One command per message" in text
    assert "git --version" in text, "Git may not be installed"
    assert text.index("git checkout main") < text.index("git pull") < text.index("git checkout -b")
    assert "placeholder" in text.lower()
    assert "git branch -m" in text
    assert "on_main" in text
    # eval 07: a student who only opened the issue and edited nothing walks the whole road.
    assert "Nothing edited yet: walk steps 2 to 4" in text
    assert "pull request" in text.lower()
    assert "don't worry" in text.lower()


def _git_reference_opening():
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    return text[text.index("Open with this") : text.index("Then walk these steps")]


def test_git_reference_opening_says_merge_not_pull_request():
    """conversation (2026-09-23, 'i want to start'): no pull request this early. The opening says
    you merge your feature branch into main, and the mechanism comes later."""
    opening = _git_reference_opening()
    assert "pull request" not in opening.lower()
    assert "**merge**" in opening
    assert "**feature branch**" in opening and "**main branch**" in opening
    assert "later" in opening


def test_git_reference_explains_production_with_a_real_example():
    """conversation (2026-09-23): 'the version your users are using' confuses a student whose
    project runs nowhere yet. Production is the environment where the real product runs."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    assert "**production**" in text
    assert "Production is the environment" in text
    assert "facebook.com" in text
    assert "your users are using" not in text


def test_git_pull_is_explicit_and_explains_origin():
    """conversation (2026-09-23): `git pull` alone, with 'brings in anything that changed there',
    taught nothing. The command names the remote and the branch, origin gets explained, and
    a lone student hears why the command changed nothing."""
    skill = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    git = GIT_REFERENCE.read_text(encoding="utf-8")
    for text in (skill, git):
        assert "git pull origin main" in text
        assert not re.search(r"git pull(?! origin main)", text), "every pull names origin and main"
    assert "**origin**" in git
    assert "colleagues" in git
    assert "only developer" in git and ";-)" in git


def test_git_reference_lets_the_student_name_the_branch_first():
    """conversation (2026-09-23): the naming rules and the bracket warning came before the student
    typed anything, and the command arrived already filled in. Send `git checkout -b <task-branch>`
    as is, say what to put there, and keep the rules for after they ran it."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    command = text.index("git checkout -b <task-branch>")
    assert "brackets included" not in text
    assert "replace `<task-branch>` with a meaningful name" in text
    assert text.index("lowercase") > command, "naming rules come after the command"
    assert text.index("t010-say-hello") > text.index("## Mistakes to catch"), "example names live with the fixes"
    assert "No example name, no naming rules" in text
    assert "Let the student try" in text
    assert text.index(";-)") > text.index("git pull origin main"), "the wink comes after the pull ran"


def test_only_the_agent_runs_e0():
    """conversation (2026-09-23, 'am i ready to start?'): the agent told the student to 'run e0
    check'. The student never runs e0; the agent runs it and says what it means."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "You run `e0 check`" in text
    assert "never ask the student to run it" in text
    assert not re.search(r"student[^.]*\bruns `e0", text), "no sentence has the student run e0"


def test_learning_skill_orients_on_every_open_task_and_skips_what_comes_next():
    """SKILL.md comments (2026-09-23): list every task in progress and every ready task, both
    plural; 'what comes next' is redundant and waits for the student to ask."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "every task in progress, each with its issue URL linked, and every task ready to start" in text
    assert "when they ask" in text
    assert "what comes next" not in text.lower()


def test_learning_skill_handles_a_task_started_out_of_order():
    """SKILL.md comment (2026-09-23): a student who starts from a later task hears which tasks
    they skipped, may choose to ignore them, and then the reminder sleeps."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "`dependency`" in text
    assert "suggest skipping them" in text
    assert "e0 dismiss <id>" in text


def test_learning_skill_reads_the_working_tree_from_status_git():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    for fact in ("status.git", "uncommitted", "conflicts", "unpushedCommits", "unclear_branch"):
        assert fact in text, f"skill does not mention {fact}"


def test_git_reference_has_a_template_for_every_scenario_e0_names():
    """git.md comments (2026-09-23): 'write here the exact format for ALL scenarios so the
    coding agent and haiku will not guess'. Every section e0 points at exists, and each holds
    a quoted template."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    named_by_e0 = set(re.findall(r"Follow '([^']+)' in", E0_PATH.read_text(encoding="utf-8")))
    assert named_by_e0 == {"Commits on main", "Uncommitted work on main", "Unclear branch"}
    sections = {
        "Git is missing",
        "The branch, step by step",
        "The short walk",
        "Several tasks, on main",
        "Unclear branch",
        "Uncommitted work on main",
        "Commits on main",
        "Checkout aborted",
        "Merge conflict",
    }
    assert named_by_e0 <= sections
    for section in sections:
        assert re.search(rf"^##+ {re.escape(section)}$", text, re.MULTILINE), f"no section {section}"
        body = text.split(f" {section}\n", 1)[1].split("\n## ", 1)[0]
        assert "\n> " in body, f"{section} has no template"
    assert "## Which scenario" in text
    assert "the templates are the lesson" in text


def test_git_reference_opening_is_titled_using_git():
    """git.md comment (2026-09-23): '‼️ Important' becomes 'Using Git'."""
    opening = _git_reference_opening()
    assert "**Using Git**" in opening
    assert "Important" not in opening and "‼️" not in opening


def test_git_reference_short_walk_reminds_and_the_full_walk_explains():
    """git.md comment (2026-09-23): on a later task the agent reminds ('we never work directly
    on main, remember?'), gives why, and offers the full explanation when the student is stuck."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    short = text.split("## The short walk", 1)[1].split("\n## ", 1)[0]
    assert "remember?" in short
    assert "never work directly on `main`" in short
    assert "**production**" in short
    assert "offer the full explanation" in short
    assert short.count("```bash") == 3, "three commands, one message each"


def test_git_reference_handles_several_open_issues():
    """git.md comment (2026-09-23): several issues open and on main: choose one. On a branch
    whose name says nothing (test123): say so, ask which task, suggest a telling name."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    on_main = text.split("## Several tasks, on main", 1)[1].split("\n## ", 1)[0]
    assert "Which one do you want to work on now?" in on_main
    unclear = text.split("## Unclear branch", 1)[1].split("\n## ", 1)[0]
    assert "does not tell me which one" in unclear
    assert "helps both of us" in unclear
    assert "git branch -m" in text


def test_git_reference_reflects_uncommitted_and_committed_work_on_main():
    """git.md comments (2026-09-23): say what they did, why main is off limits (production, no
    review, no tests), what is at stake, and the two ways out: keep or drop."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    uncommitted = text.split("### Uncommitted work on main", 1)[1].split("\n### ", 1)[0]
    assert "remember?" in uncommitted and "no review and no tests" in uncommitted
    assert "**Keep the changes**" in uncommitted and "**Throw the changes away**" in uncommitted
    assert "git checkout -b <task-branch>" in uncommitted and "git restore ." in uncommitted
    committed = text.split("### Commits on main", 1)[1].split("\n## ", 1)[0]
    assert "origin/main: what GitHub has" in committed, "a graph the student can see"
    assert "**Move the commits**" in committed and "**Drop the commits**" in committed
    assert "git reset --keep origin/main" in committed
    assert "git reset --hard" not in text


def test_git_reference_explains_an_aborted_checkout_and_offers_the_simulator():
    """git.md comment (2026-09-23): why checkout sometimes works and sometimes aborts, commit
    over stash, and a graphical demonstration served from the skill's assets."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    section = text.split("## Checkout aborted", 1)[1].split("\n## ", 1)[0]
    assert "would be overwritten by checkout" in section
    assert "protecting your work" in section
    assert "sometimes works and sometimes does not" in section
    assert "**Commit first**" in section and "**Stash**" in section
    assert "This is what we recommend" in section
    assert "http.server" in section and "checkout.html?branch={branch}&target={target}&file={file}" in section
    assert "cannot see an aborted checkout" in text, "e0 does not know; the pasted error does"


def test_checkout_simulator_exists_and_takes_the_students_names():
    asset = SKILLS / "learning" / "assets" / "checkout.html"
    html = asset.read_text(encoding="utf-8")
    for param in ("branch", "target", "file"):
        assert f'params.get("{param}")' in html
    assert "would be overwritten by checkout" in html
    assert "git stash pop" in html
    assert "<script src=" not in html and "https://" not in html, "self-contained, works offline"


def test_git_reference_explains_merge_conflicts_from_status():
    """git.md comment (2026-09-23): say it when status shows a conflict, even unasked; the lone
    developer case; conflicted vs merged files; the VS Code merge editor; then commit; the
    stage sends beginners to the tutorials."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    section = text.split("## Merge conflict", 1)[1]
    assert "even if the student did not mention it" in section
    assert "only developer here" in section
    assert "<<<<<<<" in section and "already staged" in section
    assert "Merge Editor" in section
    assert "git add <file>" in section
    assert "e0 read <topic>" in section


def test_learning_skill_links_its_references_from_the_repo_root():
    """eval 12 (2026-09-23): the agent reads SKILL.md as a plain file from the repo root, and haiku
    looked for `references/git.md` under `.exit0/`, gave up, and taught from the start template.
    Every link to a reference names the full path."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "](references/" not in text
    assert "](.exit0/skills/learning/references/git.md)" in text
    assert "](.exit0/skills/learning/references/setup-and-update.md" in text
    assert ".exit0/skills/learning/references/git.md" in E0_PATH.read_text(encoding="utf-8")


def test_learning_skill_bolds_new_terms():
    """conversation (2026-09-23): always bold a new term the first time (Git, origin, merge...)."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "Bold every new term" in text


def test_nothing_the_student_reads_says_unlock():
    """conversation.md: tasks build on each other; 'unlock' makes the course sound like a game."""
    for path in (E0_PATH, *skill_files()):
        assert "unlock" not in path.read_text(encoding="utf-8").lower(), f"{path} says unlock"


def test_learning_skill_links_the_issue_url():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "issue URL" in text


def test_learning_skill_links_only_what_exists():
    """conversation (2026-09-23): 'T010: Say hello' was a link before the task file existed, so
    clicking it did nothing. Links go only to files on disk and to issues and PRs by URL."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "Link only what exists" in text
    assert "plain text" in text


def test_learning_skill_start_message_keeps_its_paragraphs():
    """conversation (2026-09-23): the tip and the branch note ran into one block. The template
    is a literal to copy, blank lines included."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "blank lines included" in text
    assert "<issue URL>\n\n💡 Tip" in text
    assert "Markdown preview.\n\nYour first move" in text


def test_learning_skill_never_sends_the_student_to_skill_files():
    """conversation (2026-09-23): the agent told the student to 'go to git.md and follow the
    steps'. The skill and its references are for the agent; the student never hears of them."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "never link them or send the student to read them" in text
    assert "replace the branch part with [git.md]" not in text
    assert "in your own words" in text


def test_setup_reference_has_no_permission_nag():
    """From conversation.md: the 'allow e0 to run without asking' note is gone."""
    text = SETUP_REFERENCE.read_text(encoding="utf-8").lower()
    assert "without asking" not in text
    assert "allow" not in text


def test_learning_skill_stays_compact():
    """A stated goal: the skill is as short as it can be. Raise this bound only on purpose."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 100, "SKILL.md grew; prune before adding"
    assert len(text) <= 7000


def test_release_workflow_publishes_the_pinned_version():
    """Every push to main that changes e0 must create the tag the skill downloads."""
    workflow = ROOT / ".github" / "workflows" / "release.yml"
    assert workflow.exists()
    text = workflow.read_text(encoding="utf-8")
    assert "E0_VERSION" in text
    assert "gh release create" in text
    assert "cli/bin/e0" in text


def test_the_pinned_version_matches_every_release_the_setup_reference_downloads():
    """Both name the same git tag: e0 fetches its skills from the ref it was released as."""
    setup = SETUP_REFERENCE.read_text(encoding="utf-8")
    releases = set(re.findall(r'RELEASE="?(v[0-9][0-9.]*)"?', setup))
    version = re.search(r'^E0_VERSION = "(\S+)"', E0_PATH.read_text(encoding="utf-8"), re.MULTILINE).group(1)
    assert releases, "the setup reference must pin a release"
    assert releases == {version}
