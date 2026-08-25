---
name: setup-and-update
description: Use when e0 is not installed (first session in this repo), or when asked to update, or when e0 status reports that the current version should be updated.
---

# Setup and Update

## First-time setup

If the `.exit0/e0` file is missing, you should greet the student and explain what is about to run using the following template:

> Welcome to the {project name} course!
>
> Before we start, we're going to download a small tool called `e0` — a Python script that helps manage your course. It fetches content, assigns you tasks through GitHub Issues, and tracks your progress.
>
> It will live in a `.exit0/e0` folder in your repo. That folder is for internal course use — you can safely ignore it throughout the course.

> You don't need to use `e0` directly — your coding assistant will use it on your behalf.
>
> {thank-like phrase in the user language}

Then run:

```bash
RELEASE=v1.0
curl -fsSL "https://raw.githubusercontent.com/exit0-io/e0/${RELEASE}/cli/bin/e0" -o .exit0/e0 && chmod +x .exit0/e0
.exit0/e0 init
```

After `init` you MUST complete:
1. Recommend the student to allow `.exit0/e0` to run without confirmation.
2. Suggest switching to the cheapest available model. The course supplies all content, tests, and rules — you are not reasoning from scratch.
3. Continue with the `learning` skill.

## Updating

> Never update silently — tell the student what you did and why.

When the student asks to update `e0`, or when `e0 status` reports that the current version should be updated:

1. Find the target version. If you were given one in the `e0 status` output, use it. Otherwise use the latest release.
2. Run:

```bash
RELEASE=<target version>
curl -fsSL "https://raw.githubusercontent.com/exit0-io/e0/${RELEASE}/cli/bin/e0" -o .exit0/e0 && chmod +x .exit0/e0
```

3. Run `e0 status` to confirm it works, then continue with the `learning` skill.

Do not update unless the student has asked or the `e0 status` output says the current version should be updated.

