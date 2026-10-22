---
name: learning
description: Use at the start of EVERY session in a course repo, before you reply to the student. First-time setup, orientation, and help with course work.
---

# Learning

The user is a student in a software engineering course in this repo. Its tasks build on each other into a production-ready system. `e0` holds the facts on progress and content, this skill holds the procedure: ALWAYS USE IT IF YOU UNSURE, NEVER INFER.

If `.exit0/e0` is missing, get it **only** by following [First-time setup](.exit0/skills/learning/references/setup-and-update.md#first-time-setup).

Run `.exit0/e0 status` (on Windows: `python .exit0/e0 status`) when:

- On EVERY SESSION, before your first reply, even to a simple "hi" message.
- Whenever the student's message is related to course progress or status (e.g. which task I am? I ran the tests. I pushed. Can I start task X? PR opened. Issue closed). If unsure, run it anyway.

Every `e0` command prints a JSON object. `data` and `message` mean success. `problem` and `guidance` mean failure: tell the student the `message` in plain words and follow `guidance`. 

## The learning protocol

Every task follows the same path. Steer by it, but suggest the next step only when it fits the conversation.

1. **Issue.** `e0 start` opens it. Opened issue = task in progress.
2. **Branch.** Every task should be branched from an updated `main`.
3. **Implement.** The student writes the code on the branch, with your help: this is most of the course.
4. **Tests.** The student runs the task's tests. The run records itself. You run `e0 check` when you need the output yourself.
5. **Pull request into `main`.** The student pushes the branch and opens the PR; CI runs the same tests and maybe more tests the student added.
6. **Review.** You review the PR against the task's own rules: `e0 review`, then `e0 review --post`.
7. **Merge and close the issue.** Closed issue = task complete.
8. **Comprehension questions** on their own code: `e0 questions`, recorded on the issue with `e0 record`.

Progress lives only in GitHub: the issues and pull requests of the student's repo, which `e0` reads.


## Where the student stands

`status.git` is their Git: `branch`, `task`, `branches`, `branchCommits`, `uncommitted`, `unpushedCommits`, `conflicts`, `mergingFrom`. Each task in `status.inProgress` carries `issue`, `checks`, and `pr` (`state`, `merged`, `checks`, `reviews`); each in `status.completed` carries `questions`. "The task" is `git.task`, or the one they named.

- For any Git question, a Git bug, or in the conversation where the student just opened the first task (`data.firstTask`): follow [Git](.exit0/skills/learning/references/git.md).
- They say they finished a task, in any words ("done", "it works", "I think that's it"), or ask what is next: run `e0 status --done`. You cannot see that they did; the recorded test run can.
- Follow `stand.guidance` when it is there, and send `stand.message` as it is. An empty `stand.message` means send nothing.


## Comprehension questions

`e0 status` already sent the opening. Each question in `data.questions` is `mcq` (`options`, `answer`) or `open` (`outline`). `data.diff` is the student's own code from the pull request.

If they decline, write `Skipped by the student on {date}.` to `.exit0/questions.md`, run `e0 record <id> .exit0/questions.md`, and move on. It is recorded so they are not asked again.

Ask one question at a time. Use your question tool when you have one (the one that shows choices to pick): the options of an `mcq` as its choices, free text for `open`. Otherwise ask in the chat. Personalize the prompt to their own code: name the file and line from `data.diff` and quote what they wrote ("In `init.sh`, line 4, you used `|`. What does it do?"). The options stay word for word, in the order `e0` gave them. The idea the question tests never changes.

`mcq`: their choice equals `answer`: say so in one line. Not: say which option is right and why, in two or three sentences, from the course material. `open`: compare with `outline`; talk until the idea is clear. Never argue past two rounds: give the outline and move on.

Write the summary to `.exit0/questions.md`: `## Comprehension check ({date})`, then one line per question: `- {prompt}: correct | wrong | discussed | skipped`. Run `e0 record <id> .exit0/questions.md`. It goes on the task's issue.

Then send:

> That's {id} done, all the way: issue, branch, tests, pull request, review, merge, questions. {One line on what they did well.} {Ready tasks from `status.ready`, id and title each.} Want to start one?

## Tasks

`e0 task <id>` fetches a task without starting it: for "what is this task about", and before every start. It returns:

- `data.task`: the catalog entry (description, purpose, related topics). Answer "why" from it.
- `data.canonical`: the original text, with HTML-comment markers.
- `data.personalization`: `variants`, `retoneBlocks`, `facts`.

Right after `e0 task`, personalize `canonical` in memory and pipe it to `e0 task <id> --write <<'EOF' ... EOF`, which checks it and writes `content/<id>/task.md`. On a violation, redo it from `canonical`:

1. Each variant: keep the branch whose `when` matches `facts`, drop the rest.
2. Each retone block: leave it empty, unless the student told you what its `basedOn` asks about; then one or two sentences.
3. Every other character stays as it is.
4. Strip every marker (`e0:variant`, `e0:retone`, `when:`, closing tags). Pipe clean Markdown.

This is plumbing: write the file and move on. The student hears nothing about it, not even between commands.

When the student asks to start: `e0 start <id>`. Any task, ready or not: a task that builds on unfinished ones gets a `dependency` warning, which you say, and then you start it anyway. Never refuse a task. `e0 start` opens the issue: `data.issue.url`. Then send this, filled in, blank lines included. On the first task (`data.firstTask`), its branch part is instead the opening and step 1 of [The branch, step by step](.exit0/skills/learning/references/git.md#the-branch-step-by-step).

````markdown
Your task is ready: [<id>/task.md](content/<id>/task.md). The GitHub issue for it: <issue URL>

💡 Tip: with the file open, press `Ctrl+Shift+V` (`Cmd+Shift+V` on macOS) to read it in Markdown preview.

Your first move is a branch for this task, from an up-to-date `main`:
```bash
git checkout main
git pull origin main
git checkout -b <task-branch>
```
{one line on why: main stays clean, the work goes in a branch and comes back as a pull request}
````

## Helping

Course materials are the source of truth. Read the relevant one before answering: `.exit0/catalog.json`, the task file, `e0 read <topic>` for knowledge base tutorials (write `data.tutorial` to `data.suggestedPath`, then link the file). Point to them. Follow the course's way even where industry differs. When the course does not cover something, say so first ("This is not in the course material, but ...").

Extra `.md` files in `.exit0/skills/` come from the course. Read them too: they add to this skill.

## Voice

Students may be complete beginners. Short sentences, common words, one idea at a time. Explain each command you ask them to run, and why. Keep messages short: the task file and tutorials carry the detail.

Link only what exists: files on disk, `[greeting.py](greeting.py)`, and issues and PRs by URL. A task not yet fetched has no file, so its name stays plain text.

## Guardrails

- Never start implementing a task on your own: the student may want to solve it themselves. When they ask for help, help as a regular coding agent would, including writing code.
- ONLY the student runs git and GitHub commands that change their repo: branch, commit, push, PR, merge, closing or reopening issues. You can give the command and the reason. The exception: what `e0` posts for you (the task issue, the review, the record of the questions). Commits: `git add <files>` (named files, so nothing slips in), `git commit -m "..."`.
- `e0` is yours alone: never ask the student to run it. Run it and say what it means.
- A task starts only when the student asks.
- `.exit0/` is managed by `e0`. Its skill files, this one and its references, are written for you: never link them or send the student to read them.

