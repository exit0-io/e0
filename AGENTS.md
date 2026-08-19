# Working in this repository

This repo builds Exit Zero: a CLI (`e0`) and course content that give students an
agent-native learning experience. Most of what you touch here is eventually read by a
student who is still learning English, not just still learning to code.

## The one rule for anything a student reads

Write it the way a good instructor talks to a student, with deep respect for their
learning process. That means:

- Short sentences. One idea per sentence.
- Common, everyday words. Avoid idioms ("speed bump," "under the hood") and jargon
  ("idempotent," "advisory") unless you explain them in the same breath.
- Say what happened and why it matters. Don't be clever; be clear.
- If you're not sure a sentence is simple enough, read it out loud. If it doesn't sound
  like something you'd say to a person, rewrite it.

This applies to every `problem()`/`ok()` message in `agent-native/e0/bin/e0`, every file
in `agent-native/e0/skills/`, and every README or AGENTS.md a student's fork ships with.
It does not apply to code comments, commit messages, or docs in `docs/`, which are for
contributors and can use normal technical language.

## Where things live

- `agent-native/e0/` — the `e0` CLI and its skills
- `agent-native/courses/` — course templates students fork
- `docs/superpowers/specs/` and `docs/superpowers/plans/` — design and implementation
  history; read them before changing behavior they describe
