# Git

Open this for a Git question, a Git bug, or a pasted Git error, and in the conversation where the student just opened the first task. The sections below are the cases that need these exact words. If none matches, answer the question yourself, in the course's way.

## How to teach Git here

The templates below are what you send. Stick to them as closely as you can: the templates are the lesson. `{braces}` are for you to fill in.

Where a section walks numbered steps, send one step per message and wait for the student to run it before the next. "ok" or "done" is enough: trust them and move on. Ask for the output only when you think they are stuck and the output would tell you why.

## The branch, step by step

Use this in two cases only: right after `e0 start` opened the student's first issue, in this same conversation; or when, after `e0 status` sent the on-main reminder, the student asks to understand Git or branches better.

Send these messages as they are: first the opening, then each numbered step as its own message.

> **Using Git**: Engineering teams use a tool called **Git** to work on the same codebase together without stepping on each other's toes. Think about it: a code project is a collection of files, and if two people edit the same file at the same time, they can overwrite each other's work. Git solves this by letting each developer work on their own **branch** of the codebase. On a branch, your changes are separate and safe. When you are ready, you **merge** your branch into the **main branch**. We will talk later about how merging works. This is how many developers work on one project without interfering with each other.
>
> We will use Git on every task in this course. It is one of the most important tools in a developer's toolbox, and at some point you will feel at home with it.
>
> Don't worry if this is not all clear yet. We will go through it together. For now, we need one thing: your own branch (we also call it a **feature branch**) to work on this task.

1. **Switch to `main`.**

> Every task starts from the **main branch**. It holds the code that runs in **production** (f.t.t. production is the environment where the real product runs and real people use it).
>
> Take facebook.com: the code that runs there comes from the `main` branch of Facebook's codebase. Our project has no production (yet!), but `main` plays that role from day one, and every new task takes it one step further.
>
> Let's switch to the **main branch**. Run this command (you are probably on it already):
> ```bash
> git checkout main
> ```

2. **Get the latest `main`.**

> Now imagine you are part of a software team. Developers work on their own branches, and when they finish a task, they **merge** their branch into `main`.
>
> Before you start a new task, you want the most up-to-date version of `main` (that is, the most up-to-date production code). This version lives on GitHub, and you need to **pull** it into your local repository:
> ```bash
> git pull origin main
> ```
> This command says: pull the new changes of the `main` branch from the remote called **origin** (f.t.t. a remote is a copy of your repository that lives somewhere else; origin is your repository on GitHub) into your local `main` branch.
>
> You will probably see `Already up to date.` Can you tell why? Because you are the only developer on this team ;-) so nobody pushed new changes to `main` on GitHub.

3. **Create the task branch.**

> Let's create the **feature branch** on which you will work on your task:
> ```bash
> git checkout -b <task-branch>
> ```
> Replace `<task-branch>` with a meaningful name for this task.

Once they report they ran it, run `e0 status`.

## Checkout aborted

The student pastes `error: Your local changes to the following files would be overwritten by checkout`.

> Git refused to switch branches, and that is Git protecting your work. Here is what happened. Switching to `{target}` means Git rewrites the files in your folder to match `{target}`. You edited {file(s)} and did not commit. On `{target}` that file is different, so switching would overwrite your edits: Git stops instead. When the file you edited is the same on both branches, your edits simply come along and the switch works. That is why it sometimes works and sometimes does not.
>
> Two ways out:
>
> 1. **Commit first**, then switch. Your edits get a home on `{branch}`, and nothing can overwrite them. This is what we recommend: every change ends up recorded, in order.
> 2. **Stash**: put the edits aside for a moment and take them back later. We do not use it in this course; if you are curious, look up `git stash`.
>
> Want to see it happen? I can open a small interactive picture of your branches.

For 1: `git add <files>`, `git commit -m "..."`, then `git checkout {target}`.

If they want the picture: run `python3 -m http.server 8765 --directory .exit0/skills/learning/assets` in the background (another port if that one is taken) and send `http://localhost:8765/checkout.html?branch={branch}&target={target}&file={file}`. It plays both cases with their names.