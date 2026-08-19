# Working on a task

Use when the student wants to begin or continue a task.

## Starting

1. Run `e0 start <taskId>`.
2. If `warnings` contains a `dependency` entry, relay it honestly and let them choose:
   *"T020 builds on T010, which isn't done. Want to do that first, or push ahead?"*
   If they push ahead, help them — it is already recorded.
3. Personalize `task.md` using **only** what `personalization` gives you:
   - For each entry in `variants`, pick the one branch whose `when` conditions match
     `facts`. Delete the others and their `when:` markers. Never write a branch that is
     not listed.
   - Leave every `retone` block empty unless the student has explicitly asked for a note
     there. You have no basis for deciding what they already know.
   - Change nothing else. Not a word.
4. Run `e0 verify <taskId>`. If it reports violations, it has already restored the text —
   read what it says and do not repeat the mistake.
5. Open a GitHub issue using the `issue.title` and `issue.body` from `e0 start`, via `gh`
   or the GitHub MCP server, under the student's own account.
6. Point them at `.exit0/tasks/<id>/task.md` and let them read.

## While they work

The tests are already on disk, in `.exit0/tasks/<id>/checks/`. This is deliberate: read the
failing test first, then write the code that satisfies it.

Run `e0 check` when they want to know where they stand. If it reports a `check_hash`
warning, tell them their local copy of a test has drifted from the published one, so the
result may be misleading — CI always uses the original.

## Never

- Never edit files under `.exit0/` by hand; `e0` owns them.
- Never substitute a different library, tool, or approach for the one the task names. If
  the task says langchain, it means langchain, and there is a teaching reason.
- Never write the student's implementation for them. Explain, point at the failing test,
  ask what they think it wants.
