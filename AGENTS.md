# Working in this repository

This repo builds Exit Zero framework - a CLI (`e0`) that gives students an
agent-native learning experience of software engineering skills.

A student starting a software engineering course by forking a GitHub template repo, then works through it with their coding agent (just send **hi** in the chat panel to start). The agent fetches the course technical content, instructs the student task by task, runs tests or students' code, reviews PRs, and asks the student questions on its implementation. 

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
- `courses/[course-name]/content` and `courses/[course-name]/template-repo` — course content and  template repos students fork
- `docs/superpowers/specs/` and `docs/superpowers/plans/` — design and implementation
  history; read them before changing behavior they describe
