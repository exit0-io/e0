# Git

A reference for the `learning` skill. Come here when:

- the student is on their first task (`status.completed` is empty),
- the student asks for help with Git, `main`, branches, commits, or pull requests,
- `status.warnings` has `on_main`, or `status.branch` shows a Git mistake (see below).

Otherwise the short branch note in the skill is enough.

## How to teach Git here

One command per message. Say why, give the command, then wait: the student runs it and tells you what happened. Check it worked (ask for the output when unsure) and only then move to the next command. Never send the whole list at once.

On the first task, each Git term you use for the first time (branch, pull request, commit, push) gets a short note: if this is new to you, don't worry, we will cover it as we go.

`< >` marks a placeholder in every command in this course. Say so the first time you send one, and tell the student to replace the whole `<...>`, brackets included.

## The branch, step by step

Open with this on the first task (in the student's language):

> ‼️ **Important**: Engineering teams use a tool called **Git** to work on the same codebase together without stepping on each other's toes. Think about it: a project is a collection of files, and if two people edit the same file at the same time, they can overwrite each other's work. Git solves this by letting each developer work on their own **branch** of the codebase. On a branch, your changes are separate and safe. When you are ready, you open a **pull request** to bring your changes back into the main codebase. This is how many developers work on one project without interfering with each other.
>
> We will use Git on every task in this course. It is one of the most important tools in a developer's toolbox, and by the end you will feel at home with it.
>
> Don't worry if this is not all clear yet. We will go through it together. For now, we need one thing: your own branch to work on this task.

Then walk these steps, one message each:

1. **Is Git installed?** Only when the student has never run Git here: `git --version`. If the command is not found, point them to https://git-scm.com/downloads, and continue after it works.

2. **Switch to `main`.** Every task starts from the branch called `main`. Think of `main` as the code that is in production right now: the version your users are using. A new task takes that code one step further. The student works alone here, but this is the process every engineering team follows, and that is what we practice.
   ```bash
   git checkout main
   ```
   They are probably on it already (`status.branch` says); this makes sure.

3. **Get the latest `main`.** GitHub holds the shared copy of the repository. This brings in anything that changed there.
   ```bash
   git pull
   ```

4. **Create the task branch.** A good name is short, lowercase, hyphens, and says which task: `t010-say-hello`. The whole team will read it, so it must be clean and informative.
   ```bash
   git checkout -b <task-branch>
   ```
   From here on, everything for this task lives on this branch. `main` stays untouched until the pull request brings the work back.

## Mistakes to catch

`status.branch` shows what the student is actually on. Say what you see, kindly, and fix it together.

- **The placeholder was copied as is.** The branch is called `<task-branch>` or has `<` `>` in it. Very common. Explain: throughout the course `<` and `>` mark a placeholder; the brackets are not part of the name. No harm done, renaming is one command, and it matters because the team will see this name:
  ```bash
  git branch -m <task-branch>
  ```
- **Work on `main`** (`on_main` warning). If nothing is committed yet, creating the branch now carries the changes with it: step 4. If commits already landed on `main`, help them move the commits to a new branch, then bring `main` back to what GitHub has:
  ```bash
  git branch <task-branch>
  git reset --keep origin/main
  git checkout <task-branch>
  ```
