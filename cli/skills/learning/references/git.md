# Git

The exact words for each Git situation. The table in the `learning` skill maps `status.git` to a section here.

## How to teach Git here

The templates below are what you send. Stick to them as closely as you can: the templates are the lesson. `{braces}` are for you to fill in.

Where a section walks numbered steps, send one step per message and wait for the student to run it before the next. "ok" or "done" is enough: trust them and move on. Ask for the output only when you think they are stuck and the output would tell you why.

## Git is missing

> Before anything else we need **Git** on your computer. It is the tool developers use to save their work step by step and to work together on one codebase. Install it from https://git-scm.com/downloads, then tell me. To check it worked, run:
> ```bash
> git --version
> ```

Continue with the scenario you were in once the version prints.

## The branch, step by step

Use this in two cases only: right after you opened the student's first issue, in this same conversation; or when, after [On main with a task open](#on-main-with-a-task-open), the student asks to understand Git or branches better.

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

Once they report they ran it, run `e0 status` and check `git.branch` against [Branch naming issues](#branch-naming-issues).

## On main with a task open

The student has open issues (probably opened in another conversation), `git.branch` is `main`, and they are about to work on one of them. Several tasks in progress: ask which one they work on now, then continue here.

Open with:

> You are on the `main` branch, and we never work on it directly, remember? In a real-life project no one will let you work directly on `main`: it is the **production** branch. You work on each task on its own **feature branch**, then merge it into `main` through a **pull request**, so it passes the CI checks and a review.

Then `git.unpushedCommits` and `git.uncommitted` say how far they got. Continue, in the same message, with the first that matches:

**Commits on `main`** (`unpushedCommits` is above 0):

> You committed on `main`. Here is what your repository looks like right now:
>
> ```
> A --- B              origin/main: what GitHub has
>        \
>         C            main on your computer: {n} commit(s) GitHub does not have
> ```
>
> Nothing is lost. You can choose:
>
> 1. **Move the commits** to a new feature branch for this task, and put `main` back to what GitHub has.
> 2. **Drop the commits** and put `main` back to what GitHub has. Your files go back to `main`'s version.
>
> Which one?

For 1: `git branch <task-branch>` (a new branch that points at the commits), `git reset --keep origin/main` (`main` goes back to what GitHub has; the commits stay on the new branch), `git checkout <task-branch>`. For 2: `git reset --keep origin/main`, then the clean case below.

**Uncommitted work on `main`** (`uncommitted` lists files):

> You changed {the files, from `git.uncommitted`} but did not **commit** them yet, so nothing is lost and nothing is decided. Two ways out, you choose:
>
> 1. **Keep the changes** and take them with you into a new feature branch. Git carries uncommitted edits along when you create a branch.
> 2. **Throw the changes away** and start clean on a new feature branch.
>
> Which one?

For 1: `git checkout -b <task-branch>` (replace the placeholder with a meaningful name). For 2: `git restore .` (edited files go back to what `main` has; new files they delete by hand), then `git checkout -b <task-branch>`.

**Clean** (nothing above matched):

> To create your branch from an up-to-date `main`:
> ```bash
> git checkout main
> git pull origin main
> git checkout -b <task-branch>
> ```
> Replace `<task-branch>` with a meaningful name for this task.

## Unclear branch

Several issues are open and `git.task` is null: the branch name points at none of them.

> You are on the branch `{branch}`. {n} tasks are in progress ({ids and issue URLs}), and the name `{branch}` does not tell me which one this branch is for. Which task are you working on now?
>
> A branch name that says the task, like the task id and a word or two from its title, helps both of us: I can see what you work on, and so can your teammates. Once you tell me the task, we either rename this branch for it or create a fresh one.

Then, if the branch holds work for that task, [rename it](#branch-naming-issues). If not, create a new one with `git checkout -b <task-branch>` from an up-to-date `main`.

## Branch naming issues

- **The branch is called `<task-branch>` or has `<` `>` in it.**

> You included the `<` `>` in the branch name by mistake. Throughout the course `<` and `>` mark a placeholder; the brackets are not part of the name. No harm done, renaming is one command, and it matters because the team will see this name:
> ```bash
> git branch -m <task-branch>
> ```

- **The name says nothing about the task.** A good name is short, lowercase, hyphens, and says which task: `t010-say-hello`. The whole team reads it. Say what to change and give the same rename command.

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

## Merge conflict

`git.conflicts` lists the files and `git.mergingFrom` names the branch being merged in. Say it before anything else, even if the student did not mention it. Before you send it, run `python3 -m http.server 8765 --directory .exit0/skills/learning/assets` in the background (another port if that one is taken): the link in the template is `http://localhost:8765/conflict.html?branch={git.branch}&other={git.mergingFrom}&file={first file in git.conflicts}`. It replays, step by step, how two branches changed the same lines and how the merge stopped.

> I see a **merge conflict** in {files}. Don't worry: this is common, and it is fixable. It usually happens when two developers change the same lines of the same file. You are the only developer here, so it happened because the same lines were changed on two of your branches, `{branch}` and `{mergingFrom}`. To see step by step how you got here, open {link}.
>
> Git merged every file it could on its own; those are already staged, ready to commit. For {files} it could not choose, so it stopped and wrote both versions into the file between markers: `<<<<<<<`, `=======`, `>>>>>>>`. Your job: decide, for each spot, what the final text should be.
>
> VS Code helps. Open the file, click **Resolve in Merge Editor**, and for each spot choose the current version, the incoming one, both, or type the result. Then **Complete Merge**. After that:
> ```bash
> git add <file>
> ```
> and a commit, and the merge is done.
