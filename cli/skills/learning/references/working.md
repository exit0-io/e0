# Working on a task

The exact words for each stage of a task, from the branch to the merged pull request. The table in the `learning` skill maps `e0 status` to a section here. Templates are what you send; stick to them, `{braces}` are yours to fill. "The task" is the task in progress the student works on.

## Nothing in progress

No task has an open issue. Say where they are, then offer. Name a task as plain text; its file exists only after `e0 task`.

> {`status.completed` is empty: "Nothing is in progress yet." Otherwise: "{n} task(s) done, nothing in progress right now."} Ready to start: {each task in `status.ready`: id, title}. Want to start one, or hear more about one first?

Hearing more is `e0 task <id>`; starting is `e0 start <id>` (see the `learning` skill, "Tasks").

## Start or keep working

The student is on the task's branch, and the task has no pull request. `git.branchCommits` is 0 and `git.uncommitted` is empty: they have not started. Otherwise they are mid-way. If `content/<id>/task.md` is missing (a fresh clone), run `e0 task <id>` and write it first, silently.

Not started:

> You are on the branch `{branch}`, ready for {id}: {title} ({issue URL}). Want to start working on it? Tell me what you have in mind, or ask me anything about the task: [task.md](content/{id}/task.md).

Mid-way:

> You are on `{branch}` for {id}: {title} ({issue URL}), with {"{n} commit(s)" and/or "edits not committed yet in {files}"}. {If `checks.lastRun` exists: "Your last test run: {passed} of {passed + failed} pass{, failing: {failedTests}}."} Want to keep working on it?

From here the conversation is about their code: help them write it, read it, run it, and understand it. This is most of the course. Leave the workflow alone until they say they finished, in any words ("done", "it works", "I think that's it"), or ask what is next. Then go to [Tests](#tests).

## Tests

The student says they finished. You cannot see that they did; the tests can, when the task has them.

- `checks` is null: the task has no automatic tests. Ask: "This task has no automatic tests, so you are the judge. Is it done?" On yes, go to [Push and open a pull request](#push-and-open-a-pull-request).
- `checks.lastRun.passing` is true: go to [Push and open a pull request](#push-and-open-a-pull-request).
- Otherwise send:

> Before we send your work in, let's run the tests. Every task comes with **school checks** (f.t.t. school checks are small automatic tests that say whether your code does what the task asks). Run:
> ```bash
> {checks.command}
> ```
> Then tell me how it went. The run saves its result, so I can see it too.

When they report back, run `e0 status`. `lastRun.passing` true: on to the pull request. False:

> {failed} of {passed + failed} checks fail: {failedTests}. {One line per failing test on what it expects, from its name and the task.} Let's look at the code together. Where do you want to start? You can also paste the error you got.

Then help with the code, and back to the tests when they are ready. `e0 check` runs the same tests when you need to see the output yourself.

## Push and open a pull request

Two messages, in order. First, [Push the branch](git.md#push-the-branch); wait for "done". Then, before you send the second, run `e0 read pull-requests` and write `data.tutorial` to `content/knowledge-base/pull-requests.md`, so the link works. If the course has no such topic, send the same words without the link.

> Now, [open a pull request](content/knowledge-base/pull-requests.md) from `{branch}` into `main`. A **pull request** (f.t.t. a pull request is a request to merge your branch into main: the team sees the change, the tests run on it, and someone reviews it before it goes in) is how work reaches production in every team. The link explains it and shows how to open one on GitHub, step by step. Name it `[{id}] {title}`, and write `Closes #{issue number}` in the description so GitHub links it to your issue. Tell me when it is open.

When they say it is open (in any words), run `e0 status`: the task's `pr` appears, and the table says what comes next.

## CI is not green

The task has an open pull request and `pr.checks` is `failing` or `pending`. Send the template first. The fix is the student's: they edit, commit, and push. You explain, and look at the failing test with them when they ask.

`pending`:

> Your pull request is open: {pr.url}. The checks on it are still running. **CI** (f.t.t. CI, continuous integration, is a service that runs the tests on every push, so a broken change is caught before it is merged) runs the same school checks you ran. Give it a minute, then tell me.

`failing`:

> Your pull request is open: {pr.url}, but its checks are red. **CI** (f.t.t. CI, continuous integration, is a service that runs the tests on every push, so a broken change is caught before it is merged) ran the school checks on your branch, and some fail. A pull request is merged only when its checks pass; that is the rule in every team, and here too. On the pull request page, click **Details** next to the red cross and read which test failed. Fix it on `{pr.branch}`, commit, push, and the pull request updates itself. Want to look at the failing test together?

## Review

The task has an open pull request, `pr.checks` is `passing` or `none`, and `pr.reviews` is 0. Review it now; the student does not need to ask.

1. Run `e0 review <id>`. `data.diff` is the pull request; `data.rules.course` and `data.rules.task` are the whole standard.
2. Write the review, in Markdown, to `.exit0/review.md`. Check the diff against each rule and nothing else: no general best practices, no style you would prefer. Heading `## Review of {id}`, then one bullet per rule: met or not, and the line of code that shows it. Close with what to change, or "Nothing to change".
3. Run `e0 post-review <id> .exit0/review.md`. It posts the review on the pull request.
4. Send:

> I reviewed your pull request against the rules of this task and left my notes there: {pr.url}. {One or two sentences: what is good, and what to change, if anything.} Read the comments. If something needs a change: fix it, commit, push, and tell me; the pull request updates itself and I will look again. If nothing does, you can merge.

A student may ask for a review again after changes: do it again, the same way.

## After the review

The task has an open pull request and `pr.reviews` is above 0.

> Your pull request has my review on it: {pr.url}. Did you go through the comments? If something still needs a change: fix it, commit, push, and tell me, and I will review again. If it is all good: **merge** it. On the pull request page, click **Merge pull request**, then **Confirm merge**. Delete the branch when GitHub offers; its work is in `main` now. Then tell me.

When they say it is merged, run `e0 status` and follow the table.

## Close the issue

The task's `pr` is merged and its issue is still open. Closed issue = task complete, so this is the last step of the task.

> Your pull request is merged: {id} is part of `main` now. 🎉 One last thing: close the issue {issue URL}, on GitHub or with:
> ```bash
> gh issue close {issue number}
> ```
> A closed issue is how we mark a task complete. Tell me when it is done.

Then run `e0 status`: the task moves to `completed`, and its `questions` say whether to continue with [Comprehension questions](#comprehension-questions).

## Comprehension questions

A task in `status.completed` has `questions` `pending`. Ask once, right away, before offering the next task.

1. Run `e0 questions <id>`. Each question in `data.questions` is `mcq` (`options`, `answer`) or `open` (`outline`). `data.diff` is the student's own code from the pull request.
2. Send:

> Before we move on, a few questions about what you built in {id}. They are not a test; they help the ideas stick. Ready?

If they decline, write `Skipped by the student on {date}.` to `.exit0/questions.md`, run `e0 record <id> .exit0/questions.md`, and move on to [Nothing in progress](#nothing-in-progress). It is recorded so they are not asked again.

3. Ask one question at a time. Use your question tool when you have one (the one that shows choices to pick): the options of an `mcq` as its choices, free text for `open`. Otherwise ask in the chat. Personalize the prompt to their own code: name the file and line from `data.diff` and quote what they wrote ("In `init.sh`, line 4, you used `|`. What does it do?"). The options stay word for word, in the order `e0` gave them. The idea the question tests never changes.
4. `mcq`: their choice equals `answer`: say so in one line. Not: say which option is right and why, in two or three sentences, from the course material. `open`: compare with `outline`; talk until the idea is clear. Never argue past two rounds: give the outline and move on.
5. Write the summary to `.exit0/questions.md`: `## Comprehension check ({date})`, then one line per question: `- {prompt}: correct | wrong | discussed | skipped`. Run `e0 record <id> .exit0/questions.md`. It goes on the task's issue.
6. Send:

> That's {id} done, all the way: issue, branch, tests, pull request, review, merge, questions. {One line on what they did well.} {Ready tasks from `status.ready`, id and title each.} Want to start one?
