# Git Branching

A reference for the `learning` skill. Send the message below in place of the short branch note when:

- this is the student's first task (`status.completed` is empty), or
- the student asks why they need a branch, or what Git, `main`, or a pull request is, or
- you see the student working directly on `main`, or skipping the branch step.

Otherwise the short note in the skill is enough. Fill in `<task-branch>`, and keep the student's language.

> ‼️ **Important**: Engineering teams use a tool called **Git** to work on the same codebase together without stepping on each other's toes. Think about it: a project is a collection of files, and if two people edit the same file at the same time, they can overwrite each other's work. Git solves this by letting each developer work on their own **branch** of the codebase. On a branch, your changes are separate and safe. When you are ready, you open a **pull request** to bring your changes back into the main codebase. This is how many developers work on one project without interfering with each other.
>
> We will use Git on every task in this course. It is one of the most important tools in a developer's toolbox, and by the end you will feel at home with it.
>
> Don't worry if this is not all clear yet. We will go through it together. For now, we need one thing: your own branch to work on this task.
>
> Every task starts from a branch called **`main`**. Think of `main` as the code that is in **production** right now: the version your users are using. A new task takes that production code one step further, so we start from the most up-to-date `main` we can get. You are working alone here, but this is the process every engineering team follows, and that is what we are practicing.
>
> Three commands:
>
> ```bash
> git checkout main
> ```
> Switch to the `main` branch. You are probably already on it, but this makes sure.
>
> ```bash
> git pull
> ```
> Fetch the latest `main` from GitHub. GitHub holds the shared copy of the repository, so this brings in anything that changed there since you last looked.
>
> ```bash
> git checkout -b <task-branch>
> ```
> Create a new branch named `<task-branch>` and switch to it. From here on, everything you do for this task lives on this branch. `main` stays untouched until your pull request brings the work back.
>
> Run these three commands, then let me know when you're ready to code.
