# Git

A reference for the `learning` skill. Come here when:

- the student is on their first task (`status.completed` is empty),
- the student asks for help with Git, `main`, branches, commits, merges, or pull requests,
- `status.warnings` has `on_main`, or `status.branch` shows a Git mistake (see below).

Otherwise the short branch note in the skill is enough.

## How to teach Git here

One command per message. Say why, give the command, then wait: the student runs it and tells you what happened. Check it worked (ask for the output when unsure) and only then move to the next command. Never send the whole list at once.

On the first task, each Git term you use for the first time (branch, merge, commit, push) gets a short note: if this is new to you, don't worry, we will cover it as we go. Bold every term the first time it appears: **Git**, **main branch**, **feature branch**, **merge**, **origin**.

`< >` marks a placeholder in every command in this course. Send the command with the placeholder in it, and say only what to put there. Let the student try; the naming rules and the bracket mistake wait until they ran it or ask for help.

## The branch, step by step

Open with this on the first task (in the student's language):

> ‼️ **Important**: Engineering teams use a tool called **Git** to work on the same codebase together without stepping on each other's toes. Think about it: a project is a collection of files, and if two people edit the same file at the same time, they can overwrite each other's work. Git solves this by letting each developer work on their own **branch** of the codebase. On a branch, your changes are separate and safe. When you are ready, you **merge** your **feature branch** into the **main branch**. We will talk later about how merging works. This is how many developers work on one project without interfering with each other.
>
> We will use Git on every task in this course. It is one of the most important tools in a developer's toolbox, and by the end you will feel at home with it.
>
> Don't worry if this is not all clear yet. We will go through it together. For now, we need one thing: your own branch to work on this task.

Then walk these steps, one message each:

1. **Is Git installed?** Only when the student has never run Git here: `git --version`. If the command is not found, point them to https://git-scm.com/downloads, and continue after it works.

2. **Switch to `main`.** Every task starts from the **main branch**. It holds the code that runs in **production**. Production is the environment where the real product runs and real people use it. Take facebook.com: the code that runs there comes from the `main` branch of Facebook's codebase. Our project has no production yet, but `main` plays that role from day one, and every new task takes it one step further.
   ```bash
   git checkout main
   ```
   They are probably on it already (`status.branch` says); this makes sure.

3. **Get the latest `main`.** Imagine a team: while you work, your colleagues finish their tasks and merge their branches into `main`. Before you start a new task, you want the most up-to-date version. It lives on GitHub, the place developers push their code to and pull it from. Git calls that place **origin**: your project as GitHub sees it.
   ```bash
   git pull origin main
   ```
   Read it out: pull the new changes of the `main` branch from the remote called `origin`. They will report `Already up to date.` Your next message starts with this, in your words:

   > You are the only developer on this team ;-) so nobody pushed new changes and the command changed nothing. In a team it would.

4. **Create the task branch.** Give the command as is, and say: replace `<task-branch>` with a meaningful name for this task. No example name, no naming rules.
   ```bash
   git checkout -b <task-branch>
   ```
   From here on, everything for this task lives on this branch. `main` stays untouched until the work is merged back. Once they ran it, look at `status.branch` and catch the mistakes below.

## Mistakes to catch

`status.branch` shows what the student is actually on. Say what you see, kindly, and fix it together.

- **The placeholder was copied as is.** The branch is called `<task-branch>` or has `<` `>` in it. Very common. Explain: throughout the course `<` and `>` mark a placeholder; the brackets are not part of the name. No harm done, renaming is one command, and it matters because the team will see this name:
  ```bash
  git branch -m <task-branch>
  ```
- **The name is off.** A good name is short, lowercase, hyphens, and says which task: `t010-say-hello`. The whole team reads it. Say what to change and give the same rename command.
- **Work on `main`** (`on_main` warning). Nothing edited yet: walk steps 2 to 4 as usual, one at a time. Files edited but nothing committed: step 4 alone, the branch carries the changes with it. Commits already on `main`: help them move the commits to a new branch, then bring `main` back to what GitHub has:
  ```bash
  git branch <task-branch>
  git reset --keep origin/main
  git checkout <task-branch>
  ```
