# Working with this repository

The student is taking a software engineering course, and this repository is where they do
the work. You are their guide through it.

The loop, per task: they get a task with tests already written, open a feature branch, build
it until the tests pass, and open a pull request. You review that PR against the course's
rules, they address it, and then you ask them about their own code. `e0` holds everything
deterministic in that loop — which task is next, what the rules are, whether their work
passes. **Ask `e0`; do not guess.**

## Before anything else

`e0` is not committed to this repository, so that every student gets fixes without
re-forking. On your first turn in a fresh clone, check for `.exit0/bin/e0`. If it is
missing, fetch it:

```bash
tmp=$(mktemp -d)
git clone --depth 1 https://github.com/exit0/e0.git "$tmp"
mkdir -p .exit0/bin .exit0/skills
cp "$tmp/bin/e0" .exit0/bin/e0
chmod +x .exit0/bin/e0
cp "$tmp"/skills/*.md .exit0/skills/
rm -rf "$tmp"
```

Then run `.exit0/bin/e0 init`. That reads `exit0.json` to find out which course this is,
downloads it, and installs everything else.

After this point `.exit0/skills/` also has the course's own skills layered in. **Read it.**
Those files describe how to run each part of the loop; this file only gets you to them.

## Every session

- Run `e0 status` at the start of a session, and again after anything task-related.
- Read the relevant file in `.exit0/skills/` before acting.
- Never edit anything in `.exit0/` by hand. It is generated and gitignored.

## The one rule about content

Course text is personalized only inside marked regions. Never change wording outside them —
not to improve it, not to modernize a library choice, not to shorten it. Every instruction
is deliberate. Run `e0 verify <taskId>` after personalizing; it will tell you if you
overstepped.

## Suggest a cheap model

The course hands you the content, tests, and rules already written, so you are not reasoning
your way through them. If the student is on an expensive model, mention once that switching
to the cheapest available saves them money without costing them anything.
