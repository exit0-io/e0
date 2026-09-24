# Working in this repository

This repo builds the Exit0 framework - a CLI (`e0`) that gives students an
agent-native learning experience of software engineering skills. The name is written
**Exit0** everywhere a student or an agent can read it (not "Exit Zero").

A student starting a software engineering course by forking a GitHub template repo, then works through it with their coding agent (just send **hi** in the chat panel to start). The agent fetches the course technical content, instructs the student task by task, runs tests or students' code, reviews PRs, and asks the student questions on its implementation.

## Goals to keep in mind

- **The `learning` skill stays as compact and short as possible.** It is loaded into a cheap model on every session, and every line costs attention. Before adding a line, try to remove one. When you edit `cli/skills/learning/`, apply the `writing-great-skills` skill (prune no-ops, duplication, negation; keep one source of truth per meaning) and the `writing-clearly-and-concisely` skill (omit needless words, active voice, positive form). `cli/tests/test_skills.py` pins a length bound; raise it only on purpose.
- **`e0` holds the facts, the skill holds the procedure.** Anything deterministic (what is next, what a task says, whether checks pass) goes into `e0` and its JSON, so the agent has nothing to infer.
- **Progress lives in GitHub.** Open issue `[T010] ...` means in progress, closed means complete, PRs are linked by title or by `#<issue>`. `e0` stores nothing about progress locally.

## Reviewing agent conversations

The maintainer tests the framework by talking to it as a student and pasting the transcript
into a `conversation*.md` file at the repo root. Comments to the maintainers are written inline
in curly braces: `{ the agent should have linked the issue here }`. When you are asked to work
on such a file:

1. Read every `{ comment }` and the text around it.
2. Fix what it points at: the skill, `e0`, the course content, the template, or the docs.
3. Turn the comment into a test, at the cheapest level that pins the behaviour:
   - `cli/tests/test_skills.py` for what the skill text must say (fast, always runs);
   - the `e0` unit tests for what the JSON must contain;
   - `cli/tests/evals/*.json` for how the agent must behave, run by `test_agent_evals.py`
     against the real coding agent on a cheap model. Each scenario records which comment it
     came from in its `from` field.
4. Say which comments you could not turn into a test, and why.

## Language and style

When you write some user-facing content (including README files, `e0` outputs, etc.), please:

- Simple, straightforward language.
- As good instructor talks to a student, with deep respect for their
learning process.
- Common, everyday words. Avoid idioms unless you explain them in the same breath.
- Say what happened and why it matters. Don't be clever; be clear.
- If you're not sure a sentence is simple enough, read it out loud. If it doesn't sound
  like something you'd say to a person, rewrite it.

## Where things live

- `cli/` — the `e0` CLI and its skills
- `cli/tests/evals/` — agent eval scenarios (see above)
- `courses/[course-name]/content` and `courses/[course-name]/template` — course content and template repos students fork. Each is its own git repo. The template ships a verbatim copy of `cli/skills/learning/`; a test enforces it, so copy after every skill change.
- `docs/superpowers/specs/` and `docs/superpowers/plans/` — design and implementation
  history; read them before changing behavior they describe

## Running tests

```bash
cd cli && ../.venv/bin/python -m pytest -v                                   # unit tests, ~2 min
cd cli && E0_AGENT_EVALS=1 ../.venv/bin/python -m pytest tests/test_agent_evals.py -v   # agent evals, costs money
```

## Rules

- Never perform git commands yourself. Ask me.
