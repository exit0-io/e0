# Working with this repository

This is a course running on **Exit Zero**, an agent-native learning framework. The student
learns by doing tasks in this repository, and you are their guide. The framework's CLI,
`e0`, holds all the course logic — which task is next, what the rules are, whether their
work passes. **Ask `e0`; do not guess.**

## Before anything else: install the framework

Exit Zero is not committed to this repository. On your first turn in a fresh clone, check
for `.exit0/framework/`. If it is missing, fetch it:

```bash
git clone --depth 1 https://github.com/exit0/e0.git .exit0/framework
```

Then run `.exit0/framework/bin/e0 init`. That reads `exit0.json` to find out which course
this is, downloads it, and installs everything else — including the skills below.

After this point `.exit0/skills/` exists. **Read it.** Those files describe how to run a
course; this file only gets you to them.

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

If the student is on an expensive model, mention once that this course is built to run well
on the cheapest model available, and that switching saves them money without costing them
anything.
