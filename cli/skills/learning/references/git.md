# Git

A reference for the `learning` skill. Come here when:

- the student is on their first task (`status.completed` is empty),
- the student asks for help with Git, `main`, branches, commits, merges, or pull requests,
- `status.warnings` has `on_main` or `unclear_branch`, `status.git.conflicts` is not empty, or `status.branch` shows a Git mistake (see below),
- the student pastes a Git error.

Otherwise the short branch note in the skill is enough.

## How to teach Git here

One command per message. Say why, give the command, then wait: the student runs it and tells you what happened. Check it worked (ask for the output when unsure) and only then move to the next command. Never send the whole list at once.

On the first task, each Git term you use for the first time (branch, merge, commit, push) gets a short note: if this is new to you, don't worry, we will cover it as we go. Bold every term the first time it appears: **Git**, **main branch**, **feature branch**, **merge**, **origin**.

`< >` marks a placeholder in every command in this course. Send the command with the placeholder in it, and say only what to put there. Let the student try; the naming rules and the bracket mistake wait until they ran it or ask for help.

The templates below are what you send, in the student's language. `{braces}` are for you to fill in. `< >` stays as it is. Do not improvise a different structure: the templates are the lesson.

## Which scenario

Pick the first row that matches what `e0 status` says, and go to its section.

| What you see | Section |
|---|---|
| `e0 status` cannot find a git repository, or `git --version` fails | [Git is missing](#git-is-missing) |
| `status.git.conflicts` is not empty | [Merge conflict](#merge-conflict) |
| `on_main` with `state: committed` | [Commits on main](#commits-on-main) |
| `on_main` with `state: uncommitted` | [Uncommitted work on main](#uncommitted-work-on-main) |
| `on_main`, several tasks in progress | [Several tasks, on main](#several-tasks-on-main) |
| `unclear_branch` | [Unclear branch](#unclear-branch) |
| `on_main` on the first task, or the student asks how Git works, or the short walk left them stuck | [The branch, step by step](#the-branch-step-by-step) |
| `on_main` on a later task | [The short walk](#the-short-walk) |
| `status.branch` has `<` or `>`, or a name that says nothing | [Mistakes to catch](#mistakes-to-catch) |
| the student pastes `would be overwritten by checkout` | [Checkout aborted](#checkout-aborted) |

`e0` cannot see an aborted checkout: Git leaves no trace of it. The student's pasted error is the signal.

## Git is missing

> Before anything else we need **Git** on your computer. It is the tool developers use to save their work step by step and to work together on one codebase. Install it from https://git-scm.com/downloads, then tell me. To check it worked, run:
> ```bash
> git --version
> ```

Continue with the scenario you were in once the version prints.

## The branch, step by step

The full walk. Open with this on the first task (in the student's language):

> **Using Git**: Engineering teams use a tool called **Git** to work on the same codebase together without stepping on each other's toes. Think about it: a project is a collection of files, and if two people edit the same file at the same time, they can overwrite each other's work. Git solves this by letting each developer work on their own **branch** of the codebase. On a branch, your changes are separate and safe. When you are ready, you **merge** your **feature branch** into the **main branch**. We will talk later about how merging works. This is how many developers work on one project without interfering with each other.
>
> We will use Git on every task in this course. It is one of the most important tools in a developer's toolbox, and by the end you will feel at home with it.
>
> Don't worry if this is not all clear yet. We will go through it together. For now, we need one thing: your own branch to work on this task.

When you come here from `on_main`, add one line before the first command: right now you are on `main`, and task work never happens there, so the first and most important thing is a branch for this task; let me show you how.

Then walk these steps, one message each:

1. **Is Git installed?** Only when the student has never run Git here: `git --version`. If the command is not found, go to [Git is missing](#git-is-missing) and continue after it works.

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

## The short walk

For a later task (`status.completed` is not empty), when the student is on `main` and nothing is edited. Same three commands, one message each, one line of why each. Open with:

> You are on `main`, and we never work directly on `main`, remember? It stands for **production**: what is there is live. Task work goes on its own **feature branch** and comes back to `main` through a **pull request**. So the first move, like on every task: a fresh branch from an up-to-date `main`. First, make sure we start from `main`:
> ```bash
> git checkout main
> ```
> Tell me when it ran.

Then, one message each:

> Now the latest `main` from GitHub (**origin**), in case anything changed there:
> ```bash
> git pull origin main
> ```

> And the branch for this task. Replace `<task-branch>` with a meaningful name for it:
> ```bash
> git checkout -b <task-branch>
> ```

If they ask why, hesitate, or something fails, offer the full explanation and switch to [The branch, step by step](#the-branch-step-by-step).

## Several tasks, on main

Several issues are open and the student is on `main`. Choose before anything else:

> I see {n} tasks in progress: {one line per task: id, title, issue URL}. Which one do you want to work on now? Once you choose, we create a branch for it.

When they answer, continue with the row for `on_main` that matches their `state`. If they want to work on both, one branch per task, one at a time.

## Unclear branch

Several issues are open and `status.branch` names none of them (`branchTask` is null):

> You are on the branch `{branch}`. {n} tasks are in progress ({ids and issue URLs}), and the name `{branch}` does not tell me which one this branch is for. Which task are you working on now?
>
> A branch name that says the task, like the task id and a word or two from its title, helps both of us: I can see what you work on, and so can your teammates. Once you tell me the task, we either rename this branch for it or create a fresh one.

Then, if the branch holds work for that task, [rename it](#mistakes-to-catch). If not, create a new one with `git checkout -b <task-branch>` from an up-to-date `main`.

## Mistakes to catch

`status.branch` shows what the student is actually on. Say what you see, kindly, and fix it together.

- **The placeholder was copied as is.** The branch is called `<task-branch>` or has `<` `>` in it. Very common. Explain: throughout the course `<` and `>` mark a placeholder; the brackets are not part of the name. No harm done, renaming is one command, and it matters because the team will see this name:
  ```bash
  git branch -m <task-branch>
  ```
- **The name is off.** A good name is short, lowercase, hyphens, and says which task: `t010-say-hello`. The whole team reads it. Say what to change and give the same rename command.
- **Work on `main`** (`on_main` warning). Its `state` says how far they got. Nothing edited yet: walk steps 2 to 4 as usual, one at a time (full walk on the first task, short walk later). Otherwise, the two sections below.

### Uncommitted work on main

`on_main` with `state: uncommitted`. `status.git.uncommitted` lists the files.

> Oops: you are working on `main`, and we never work on `main`, remember? It stands for **production**. You could commit here, but in a real team nobody would let you push straight to `main`: that is pushing code into production with no review and no tests. You changed {the files, from `status.git.uncommitted`} but did not **commit** them yet, so nothing is lost and nothing is decided. Two ways out, you choose:
>
> 1. **Keep the changes** and take them with you into a new feature branch. Git carries uncommitted edits along when you create a branch.
> 2. **Throw the changes away** and start clean on a new feature branch.
>
> Which one?

Then, one command per message. For 1: `git checkout -b <task-branch>` (replace the placeholder with a meaningful name). For 2: `git restore .` (edited files go back to what `main` has; new files they delete by hand), then `git checkout -b <task-branch>`.

### Commits on main

`on_main` with `state: committed`. `status.git.unpushedCommits` counts the commits GitHub does not have.

> Oops: you committed on `main`, and we never work on `main`, remember? It stands for **production**. Here is what your repository looks like right now:
>
> ```
> A --- B              origin/main: what GitHub has
>        \
>         C            main on your computer: {n} commit(s) GitHub does not have
> ```
>
> In a real team nobody would let you push these commits to `main` on GitHub: that is pushing code into production with no review and no tests. Nothing is lost, and you choose:
>
> 1. **Move the commits** to a new feature branch for this task, and put `main` back to what GitHub has.
> 2. **Drop the commits** and put `main` back to what GitHub has. Your files go back to `main`'s version.
>
> Which one?

For 1, one command per message: `git branch <task-branch>` (a new branch that points at the commits), `git reset --keep origin/main` (`main` goes back to what GitHub has; the commits stay on the new branch), `git checkout <task-branch>`. For 2: `git reset --keep origin/main` alone, then the usual branch step.

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

Then `git add <files>`, `git commit -m "..."`, `git checkout {target}`, one per message.

If they want the picture: run `python3 -m http.server 8765 --directory .exit0/skills/learning/assets` in the background (another port if that one is taken) and send `http://localhost:8765/checkout.html?branch={branch}&target={target}&file={file}`. It plays both cases with their names.

## Merge conflict

`status.git.conflicts` lists the files. Say it before anything else, even if the student did not mention it.

> I see a **merge conflict** in {files}. Don't worry: this is common, and it is fixable. It usually happens when two developers change the same lines of the same file. You are the only developer here, so it happened because the same lines were changed on two of your branches: {for example, `main` changed on GitHub when a pull request was merged, and your branch changed the same lines}.
>
> Git merged every file it could on its own; those are already staged, ready to commit. For {files} it could not choose, so it stopped and wrote both versions into the file between markers: `<<<<<<<`, `=======`, `>>>>>>>`. Your job: decide, for each spot, what the final text should be.
>
> VS Code helps. Open the file, click **Resolve in Merge Editor**, and for each spot choose the current version, the incoming one, both, or type the result. Then **Complete Merge**. After that:
> ```bash
> git add <file>
> ```
> and a commit, and the merge is done.

If "staged" or "stage" is new to them, they need the Git basics first: point them to the Git tutorial of the course (`e0 read <topic>` from the task's related topics). When the course has none, say so and explain the stage in two sentences.
