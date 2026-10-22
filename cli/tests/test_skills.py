import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILLS = ROOT / "cli" / "skills"
E0_PATH = ROOT / "cli" / "bin" / "e0"

# The learning skill is the single entry point. Everything else is a reference inside it.
EXPECTED = {"learning"}
SETUP_REFERENCE = SKILLS / "learning" / "references" / "setup-and-update.md"
GIT_REFERENCE = SKILLS / "learning" / "references" / "git.md"
WORKING_REFERENCE = SKILLS / "learning" / "references" / "working.md"

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
    # 2026-10-07: the agent pipes the personalized text through e0, which checks it before
    # writing; e0 start only opens the issue, and there is no e0 verify.
    assert text.index("e0 task <id>") < text.index("e0 task <id> --write") < text.index("e0 start <id>")
    assert "e0 verify" not in text


def test_learning_skill_reads_progress_from_github_issues():
    """2026-10-07: e0 runs every gh command and opens the task issue itself. When gh is
    missing or logged out, e0's problem message is the student text, so the skill says
    nothing about setting gh up and the agent never runs `gh issue create`."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "opened issue" in text.lower()
    assert "`e0 start` opens it" in text
    assert "gh auth" not in text
    assert "Open the issue with" not in text


def test_learning_skill_lets_e0_own_the_git_missing_message():
    """When git is missing or the folder is not a repo, e0's problem message is the student
    text, same as gh missing. The skill has no row; git.md has no section."""
    skill = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    git = GIT_REFERENCE.read_text(encoding="utf-8")
    assert "git-is-missing" not in skill
    assert "## Git is missing" not in git
    assert "cannot find a git repository" not in skill.lower()


def test_learning_skill_lets_e0_own_the_merge_conflict_message():
    """A merge conflict is a problem, same as git missing. The skill has no row; git.md
    has no section. Reading e0 already sends the message and follows guidance."""
    skill = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    git = GIT_REFERENCE.read_text(encoding="utf-8")
    assert "merge-conflict" not in skill
    assert "## Merge conflict" not in git
    assert "warning is the case" not in skill
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "merge_conflict" in e0
    assert "http.server" in e0 and "conflict.html" in e0


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
    assert "get it **only** by following [First-time setup]" in skill


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
    # conversation (2026-10-07): the words of a warning come from e0, written for the student;
    # the skill only says to send them as they are.
    assert "send `stand.message` as it is" in text
    assert "closed_without_pr" not in text and "gh issue reopen" not in text
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "closed_without_pr" in e0 and "gh issue reopen" in e0


def test_learning_skill_sends_the_student_to_a_branch_first():
    """From conversation.md: after handing over the task, the first move is a feature branch
    from an updated main, run by the student."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "git checkout -b" in text
    assert "git pull" in text
    assert "first move" in text


def test_learning_skill_sends_git_help_to_the_git_reference():
    """conversation.md: first task, a Git question, or work on main all lead to git.md, and the
    skill itself stays short. conversation (2026-09-24): the facts are status.git, and a table,
    not a warning, says what they mean. Git runs through every task, so the table sits in
    SKILL.md and each row links the full instructions in git.md."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "references/git.md" in text
    assert "status.git" in text
    assert "first task" in text.lower()
    assert "on_main" not in text and "unclear_branch" not in text and "status.branch" not in text


def test_learning_skill_says_the_first_task_exception_before_the_start_template():
    """conversation (2026-09-24): haiku copied the literal branch block of the start template on
    the first task, because the exception came after it. The exception, keyed on e0's
    data.firstTask, now comes before the template."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    stands = text.index("## Where the student stands")
    assert text.index("`data.firstTask`", stands) < text.index("data.stand"), (
        "the first-task pointer comes before later e0-determined rows"
    )
    start = text.index("When the student asks to start")
    exception = start + text[start:].index("`data.firstTask`")
    assert exception < text.index("Your first move is a branch")
    assert "git.md#the-branch-step-by-step" in text[exception:exception + 200]


def test_git_reference_teaches_one_step_at_a_time_without_nagging():
    """conversation.md: give one command, let the student run it, then the next. conversation
    (2026-09-24): 'ok' is enough; the agent asked three times for output it did not need.
    Ask for it only when the student seems stuck."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    assert "one step per message" in text
    assert "trust them and move on" in text
    assert "Ask for the output only when" in text
    assert "Never send the whole list" not in text
    assert "git --version" not in text, "Git missing is e0's message, not git.md's"
    assert text.index("git checkout main") < text.index("git pull") < text.index("git checkout -b")
    assert "placeholder" in E0_PATH.read_text(encoding="utf-8").lower()
    assert "git branch -m" in E0_PATH.read_text(encoding="utf-8")
    assert "pull request" in E0_PATH.read_text(encoding="utf-8").lower()
    assert "don't worry" in text.lower()


def test_git_reference_is_templates_not_hints():
    """git.md comment (2026-09-24): the reference is a table of cases and answers. The agent
    sends the template, it does not think up what to say; 'say why' is gone with the bold and
    placeholder paragraphs, which SKILL.md and the naming section now own."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    assert "Stick to them as closely as you can" in text
    assert "the templates are the lesson" in text
    assert "Say why" not in text
    assert "Bold every term" not in text
    assert "marks a placeholder in every command" not in text
    assert not re.search(r"\{\s", text), "a maintainer comment ({ ... }) was left in the reference"


def _section(text, title):
    return text.split(f"## {title}\n", 1)[1].split("\n## ", 1)[0]


def _skill_git_table():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    if "| What you see |" not in text:
        return ""
    start = text.index("| What you see |")
    return text[start : text.index("\n\n", start)]


def _git_reference_opening():
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    return text[text.index("Send these messages as they are") : text.index("1. **Switch to `main`.**")]


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
    assert "**production** (f.t.t. production is the environment" in text
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
    assert "**origin** (f.t.t. " in git
    assert "only developer" in git and ";-)" in git


def test_git_reference_lets_the_student_name_the_branch_first():
    """conversation (2026-09-23): the naming rules and the bracket warning came before the student
    typed anything, and the command arrived already filled in. Send `git checkout -b <task-branch>`
    as is, say what to put there, and keep the rules for after they ran it."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    command = text.index("git checkout -b <task-branch>")
    assert "brackets included" not in text
    assert "Replace `<task-branch>` with a meaningful name for this task" in text
    assert text.index(";-)") > text.index("git pull origin main"), "the wink comes after the pull ran"
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "lowercase" in e0 and "git branch -m <task-branch>" in e0
    assert "## Branch naming issues" not in text
    assert command < text.index("Once they report they ran it")


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
    assert "what comes next" not in text.lower()
    # SKILL.md comments (2026-09-24): which open task and the start offer live in e0's stand;
    # later tasks come from the catalog, and status.next is gone.
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "Which one are you working on now?" in e0
    assert "status.next" not in text
    assert ".exit0/catalog.json" in text
    assert "Want to start one, or hear more about one first?" in e0
    assert "Ready to start" in e0


def test_learning_skill_handles_a_task_started_out_of_order():
    """SKILL.md comment (2026-09-23): a student who starts from a later task hears which tasks
    they skipped, may choose to ignore them, and then the reminder sleeps."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "`dependency`" in text
    assert "e0 dismiss" in E0_PATH.read_text(encoding="utf-8")
    # conversation (2026-10-07): the suggestion to skip is in e0's message, not in the skill.
    assert "suggest skipping" not in text
    assert "Want to skip" in E0_PATH.read_text(encoding="utf-8")


def test_learning_skill_reads_the_working_tree_from_status_git():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    for fact in ("status.git", "`branch`", "`task`", "uncommitted", "conflicts", "unpushedCommits", "mergingFrom"):
        assert fact in text, f"skill does not mention {fact}"


def test_git_reference_has_a_template_for_every_scenario():
    """git.md comments (2026-09-23): 'write here the exact format for ALL scenarios so the
    coding agent and haiku will not guess'. Every section the table points at exists, and
    each holds a quoted template. conversation (2026-09-24): the table lives in SKILL.md,
    Git being part of every task, and each row links its git.md section."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    skill = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "references/git.md" in skill
    assert "checkout-aborted" not in skill, "a Git bug is the whole file, not one named case"
    assert "git.md#the-branch-step-by-step" in skill
    assert "Which scenario" not in text, "no scenario table"
    assert "## Branch naming issues" not in text
    every_section = set(re.findall(r"^## (.+)$", text, re.MULTILINE)) - {"How to teach Git here"}
    assert every_section == {
        "The branch, step by step",
        "Checkout aborted",
    }
    for section in every_section:
        assert "\n> " in _section(text, section), f"{section} has no template"
    assert "the templates are the lesson" in text


def test_git_reference_table_reads_status_git_only():
    """conversation (2026-09-24): the on_main and unclear_branch warnings duplicated status.git
    and git.md. Naming and on-branch work are e0's stand too."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    for gone in ("on_main", "unclear_branch", "warnings", "status.branch", "branchTask"):
        assert gone not in text, f"git.md still says {gone}"
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert '"on_main"' in e0 and '"unclear_branch"' in e0
    assert '"branch_brackets"' in e0 and '"start_working"' in e0
    assert '"push_branch"' in e0
    assert "Follow '" not in e0


def test_git_reference_opening_is_titled_using_git():
    """git.md comment (2026-09-23): '‼️ Important' becomes 'Using Git'."""
    opening = _git_reference_opening()
    assert "**Using Git**" in opening
    assert "Important" not in opening and "‼️" not in opening


def test_git_reference_step_by_step_is_for_the_first_issue_or_a_curious_student():
    """git.md comments (2026-09-24): the full walk runs right after the agent opened the first
    issue, in the same conversation, or when the student asks to understand Git better after
    the reminder. Nowhere else. The 'is Git installed' step is gone: e0's git_missing
    message has it."""
    text = GIT_REFERENCE.read_text(encoding="utf-8")
    walk = _section(text, "The branch, step by step")
    assert "right after `e0 start` opened the student's first issue, in this same conversation" in walk
    assert "asks to understand Git or branches better" in walk
    assert "Send these messages as they are" in walk
    assert "git --version" not in walk
    assert walk.count("```bash") == 3, "three commands, one message each"
    assert "1. **Switch to `main`.**" in walk and "3. **Create the task branch.**" in walk
    assert "you are probably on it already" in walk
    assert "Can you tell why?" in walk
    skill = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    stands = skill.index("## Where the student stands")
    assert skill.index("references/git.md", stands) < skill.index("data.stand"), (
        "the Git file still wins over later e0-determined rows"
    )


def test_git_reference_on_main_reminds_then_splits_by_what_the_student_did():
    """git.md comments (2026-09-24): open issues from another conversation, student on main:
    remind ('we never work on it directly, remember?', production, review), then one of the
    cases from status.git. The student text lives in e0's on_main stand."""
    e0 = E0_PATH.read_text(encoding="utf-8")
    git = GIT_REFERENCE.read_text(encoding="utf-8")
    assert "remember?" in e0
    assert "never work on it directly" in e0
    assert "**production**" in e0 and "pull request" in e0
    assert "Which one are you working on now?" in e0
    assert "You committed on `main`" in e0
    assert "origin/main: what GitHub has" in e0
    assert "**Move the commits**" in e0 and "**Drop the commits**" in e0
    assert "did not **commit**" in e0
    assert "**Keep the changes**" in e0 and "**Throw the changes away**" in e0
    assert "You already have a branch for this task" in e0
    assert "start over" in e0
    assert "To create your branch from an up-to-date `main`" in e0
    assert "git checkout main" in e0 and "git pull origin main" in e0
    assert "git checkout -b <task-branch>" in e0
    assert "git reset --keep origin/main" in e0
    assert "git restore ." in e0
    assert "## On main with a task open" not in git
    assert "## Uncommitted work on main" not in git and "## Commits on main" not in git
    assert "The short walk" not in git and "Mistakes to catch" not in git


def test_git_reference_handles_several_open_issues():
    """git.md comment (2026-09-23): on a branch whose name says nothing (test123): say so, ask
    which task, suggest a telling name. The student text is e0's unclear_branch stand."""
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "does not tell me which one" in e0
    assert "helps both of us" in e0
    assert "## Unclear branch" not in GIT_REFERENCE.read_text(encoding="utf-8")
    assert "git branch -m" in E0_PATH.read_text(encoding="utf-8")


def test_git_reference_reflects_uncommitted_and_committed_work_on_main():
    """git.md comments (2026-09-23): say what they did, what is at stake, and the two ways
    out: keep or drop. The student text is e0's on_main stand."""
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "**Keep the changes**" in e0 and "**Throw the changes away**" in e0
    assert "git checkout -b <task-branch>" in e0 and "git restore ." in e0
    assert "origin/main: what GitHub has" in e0, "a graph the student can see"
    assert "**Move the commits**" in e0 and "**Drop the commits**" in e0
    assert "git reset --keep origin/main" in e0
    assert "git reset --hard" not in e0


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
    skill = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "pasted Git error" in skill and "checkout-aborted" not in skill


def test_checkout_simulator_exists_and_takes_the_students_names():
    asset = SKILLS / "learning" / "assets" / "checkout.html"
    html = asset.read_text(encoding="utf-8")
    for param in ("branch", "target", "file"):
        assert f'params.get("{param}")' in html
    assert "would be overwritten by checkout" in html
    assert "git stash pop" in html
    assert "<script src=" not in html and "https://" not in html, "self-contained, works offline"


def test_git_reference_explains_merge_conflicts_from_status():
    """The student text and the simulator live in e0. git.md no longer holds this case."""
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "only developer here" in e0
    assert "<<<<<<<" in e0 and "already staged" in e0
    assert "Merge Editor" in e0
    assert "conflict.html" in e0
    assert "http.server" in e0
    assert "## Merge conflict" not in GIT_REFERENCE.read_text(encoding="utf-8")


def test_conflict_simulator_exists_and_takes_the_students_names():
    asset = SKILLS / "learning" / "assets" / "conflict.html"
    html = asset.read_text(encoding="utf-8")
    for param in ("branch", "other", "file"):
        assert f'params.get("{param}")' in html
    assert "CONFLICT (content): Merge conflict in" in html
    assert "=======" in html and "HEAD" in html
    assert "Merge Editor" in html
    assert "<script src=" not in html and "https://" not in html, "self-contained, works offline"


def test_learning_skill_links_its_references_from_the_repo_root():
    """eval 12 (2026-09-23): the agent reads SKILL.md as a plain file from the repo root, and haiku
    looked for `references/git.md` under `.exit0/`, gave up, and taught from the start template.
    Every link to a reference names the full path."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "](references/" not in text
    assert "](.exit0/skills/learning/references/git.md" in text
    assert "](.exit0/skills/learning/references/setup-and-update.md" in text


def test_learning_skill_bolds_and_defines_first_time_terms():
    """conversation (2026-09-23): always bold a new term the first time (Git, origin, merge...).
    git.md comment (2026-09-24): the author marks a first-time term as `term (f.t.t. definition)`
    in any course text; the agent bolds it and says 'since this is the first time we use this
    term, let me define it for you'. The rule lives in SKILL.md, and git.md uses the marker."""
    git = GIT_REFERENCE.read_text(encoding="utf-8")
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert re.search(r"\*\*\w+\*\* \(f\.t\.t\. ", git), "git.md templates use the marker"
    assert "(f.t.t. " in e0


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


def test_setup_reference_has_no_permission_nag():
    """From conversation.md: the 'allow e0 to run without asking' note is gone."""
    text = SETUP_REFERENCE.read_text(encoding="utf-8").lower()
    assert "without asking" not in text
    assert "allow" not in text


def test_learning_skill_stays_compact():
    """A stated goal: the skill is as short as it can be. Raise this bound only on purpose."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    # Both bounds raised on 2026-09-24 when the Git table moved here from git.md, and again on
    # 2026-09-26 when the table grew from Git alone to the whole task flow (tests, PR, CI,
    # review, merge, questions), every row with a root-relative link.
    assert len(text.splitlines()) <= 125, "SKILL.md grew; prune before adding"
    # Raised from 7000 on 2026-09-24 for the first-time-term rule and the orientation rules,
    # then to 8300 the same day for the Git table, then to 10600 on 2026-09-26 for the flow.
    assert len(text) <= 10600


# ---------------------------------------------------------------- the whole task flow
# conversation (2026-09-26): after the first conversation, every session finds the student
# somewhere on the road from the branch to the merged PR. The skill has a row for each place,
# the templates live in working.md, and the review and the questions are part of this skill.


def _skill_table_rows():
    return [row for row in _skill_git_table().splitlines()[2:]]


def test_learning_skill_has_one_table_from_git_to_questions():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "## Where the student stands" in text
    assert "| What you see |" not in text
    working = WORKING_REFERENCE.read_text(encoding="utf-8")
    linked = re.findall(r"\]\(\.exit0/skills/learning/references/working\.md#([a-z-]+)\)", text)
    assert set(linked) == {"tests"}
    for anchor in set(linked):
        title = anchor.replace("-", " ").capitalize()
        assert re.search(rf"^## {re.escape(title)}$", working, re.MULTILINE), f"no section {title}"
        assert "\n> " in _section(working, title), f"{title} has no template"
    assert "another skill" not in text, "review and questions are this skill's"


def test_learning_skill_table_rows_come_in_the_order_of_the_flow():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    stands = text.index("## Where the student stands")
    region = text[stands:]
    assert region.index("references/git.md") < region.index("working.md#tests")
    assert region.index("working.md#tests") < region.index("data.stand")


def test_learning_skill_reads_every_fact_status_gives():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    for fact in ("`branches`", "`branchCommits`", "`checks`", "`lastRun`", "`pr`", "`reviews`", "`questions`", "`command`"):
        assert fact in text, f"skill does not mention {fact}"
    assert "`merged`" in text and "`reviews`" in text
    assert "`lastRun`" in text


def test_learning_skill_runs_status_again_when_the_student_reports_a_step():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "Whenever the student's message is related to course progress" in text
    assert "If unsure, run it anyway" in text


def test_learning_skill_sends_the_template_before_acting():
    """eval 24 (2026-09-26): with CI red, haiku skipped the template, ran the checks, wrote the
    code, committed and pushed. The template comes first; the fix is the student's."""
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "before you run or fix anything" in e0
    assert "The fix is the student's" in e0
    assert "## CI is not green" not in WORKING_REFERENCE.read_text(encoding="utf-8")


def test_learning_skill_never_refuses_a_task():
    """eval 29 (2026-09-26): haiku refused 'let's start T020' because T020 was not in
    status.ready. Ready is advice; any task can be started, with the dependency warning said."""
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "Any task, ready or not" in text
    assert "Never refuse a task" in text
    assert text.index("Never refuse a task") < text.index("Your task is ready:")


def test_working_reference_splits_start_from_keep_working():
    """conversation (2026-09-26): clean branch and tree: 'start'. Commits or edits: 'keep
    working'. Then the conversation is about the code, not the workflow."""
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "Want to start working on it?" in e0
    assert "Want to keep working on it?" in e0
    assert "Your last test run:" in e0
    assert "the conversation is about their code" in e0
    assert "Leave the workflow" in e0
    assert "/task.md` is missing" in e0
    assert "## Start or keep working" not in WORKING_REFERENCE.read_text(encoding="utf-8")


def test_task_links_show_which_task_the_file_is_for():
    """conversation (2026-10-07): every task file is called task.md, so a link that reads
    'task.md' tells the student nothing. The link text names the task folder."""
    skill = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    working = WORKING_REFERENCE.read_text(encoding="utf-8")
    assert "[<id>/task.md](content/<id>/task.md)" in skill
    assert "[task.md](" not in skill and "[task.md](" not in working


def test_the_student_writes_the_code():
    """conversation (2026-10-07): the student said 'done' after the branch, and the agent read
    greeting.py and wrote the function itself. The agent never starts implementing on its own;
    once the student asks for help, it helps as a regular coding agent, code included."""
    skill = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    e0 = E0_PATH.read_text(encoding="utf-8")
    working = WORKING_REFERENCE.read_text(encoding="utf-8")
    guardrails = _section(skill, "Guardrails")
    assert "Never start implementing a task on your own" in guardrails
    assert "help as a regular coding agent would, including writing code" in guardrails
    assert "Never start implementing on your own" in e0
    assert "help as a regular coding agent would" in e0
    assert "Edit their files only when they ask" not in skill + working + e0


def test_working_reference_tests_are_run_by_the_student_and_read_by_e0():
    """conversation (2026-09-26): the agent cannot know the student finished; the recorded
    test run can. No tests: ask. Passing: on to the PR. Failing: back to the code."""
    section = _section(WORKING_REFERENCE.read_text(encoding="utf-8"), "Tests")
    assert "You cannot see that they did" in section
    assert "`checks` is null" in section and "no automatic tests" in section
    assert "`checks.lastRun.passing` is true" in section
    assert "data.stand" in section
    assert "{checks.command}" in section
    assert "The run saves its result, so I can see it too" in section
    assert "**school checks** (f.t.t. " in section
    assert "{failedTests}" in section
    assert "`e0 check` runs the same tests" in section
    skill = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    assert "The student runs `checks.command`" in skill


def test_working_reference_push_then_pull_request_with_the_tutorial_link():
    """conversation (2026-09-26): push first (git.md), then 'open a pull request' as a link to
    the knowledge base document, fetched the same way as any tutorial."""
    text = WORKING_REFERENCE.read_text(encoding="utf-8")
    section = _section(text, "Push and open a pull request")
    assert "## Push the branch" not in GIT_REFERENCE.read_text(encoding="utf-8")
    assert "`e0 read pull-requests`" in section
    assert "content/knowledge-base/pull-requests.md" in section
    assert "[open a pull request](content/knowledge-base/pull-requests.md)" in section
    assert "**pull request** (f.t.t. " in section
    assert "`[{id}] {title}`" in section and "Closes #{issue number}" in section
    assert "without the link" in section, "a course may lack the topic"
    assert "run `e0 status`" in section
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "git push -u origin" in e0
    assert "**push** (f.t.t. " in e0
    assert "`-u`" in e0 and "twin" in e0
    assert "not committed yet" in e0 and "git commit -m" in e0, "uncommitted work is committed first"


def test_working_reference_ci_must_be_green_before_the_review():
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert '"failing", "pending"' in e0 or 'checks in ("failing", "pending")' in e0
    assert "**CI** (f.t.t. " in e0
    assert "merged only when its checks pass" in e0
    assert "**Details**" in e0
    assert "Give it a minute" in e0
    assert "## CI is not green" not in WORKING_REFERENCE.read_text(encoding="utf-8")


def test_working_reference_reviews_against_the_task_rules_only_through_e0():
    """conversation (2026-09-26): not a general code review; the rules of the task are the whole
    standard, they never touch the disk, the review is posted through e0 and counted by status."""
    e0 = E0_PATH.read_text(encoding="utf-8")
    working = WORKING_REFERENCE.read_text(encoding="utf-8")
    assert "the student does not need to ask" in e0
    assert "data.rules.course" in e0 and "data.rules.task" in e0
    assert "whole standard" in e0
    assert "no general best practices" in e0
    assert "one bullet per rule" in e0
    assert "--post <<'EOF'" in e0 and "never a file" in e0
    assert "review.md" not in e0 and "review.md" not in working
    assert "gh pr review" not in e0 and "gh pr review" not in working
    assert "ask again after changes" in e0
    assert "**Merge pull request**" in e0 and "**Confirm merge**" in e0
    assert "## Review" not in working and "## After the review" not in working


def test_working_reference_closes_the_issue_after_the_merge():
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "gh issue close" in e0
    assert "A closed issue is how we mark a task complete" in e0
    assert "## Close the issue" not in WORKING_REFERENCE.read_text(encoding="utf-8")


def test_working_reference_asks_personalized_questions_and_records_them_on_the_issue():
    """conversation (2026-09-26): canonical questions, asked as if about the student's own code
    ('In init.sh line 4 you used |'), with the agent's question tool, recorded on the issue,
    and recorded as skipped when declined so they are not asked again."""
    section = _section(WORKING_REFERENCE.read_text(encoding="utf-8"), "Comprehension questions")
    e0 = E0_PATH.read_text(encoding="utf-8")
    assert "questions" in e0 and "pending" in e0
    assert "e0 questions" in e0
    assert "`mcq` (`options`, `answer`)" in section and "`open` (`outline`)" in section
    assert "question tool" in section
    assert "one question at a time" in section
    assert "name the file and line from `data.diff`" in section
    assert "In `init.sh`, line 4, you used `|`" in section
    assert "The options stay word for word" in section
    assert "The idea the question tests never changes" in section
    assert "`e0 record <id> .exit0/questions.md`" in section
    assert "Skipped by the student" in section and "not asked again" in section
    assert "correct | wrong | discussed | skipped" in section
    assert "Ready?" in e0


def test_working_reference_is_templates_with_no_maintainer_comments():
    text = WORKING_REFERENCE.read_text(encoding="utf-8")
    assert not re.search(r"\{\s", text), "a maintainer comment ({ ... }) was left in the reference"
    assert "Templates are what you send" in text


def test_learning_skill_lets_e0_post_the_review_and_the_record():
    text = (SKILLS / "learning" / "SKILL.md").read_text(encoding="utf-8")
    guardrails = _section(text, "Guardrails")
    assert "what `e0` posts for you (the task issue, the review, the record of the questions)" in guardrails
    assert "merge" in guardrails, "the student merges"


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
