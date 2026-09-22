# Setup and Update

A reference for the `learning` skill. You come here from "Every session" and go back there when you finish.

## First-time setup

If `.exit0/e0` is missing, the student is taking their first step in the course. Greet them with this template. The course name is the title of the repo's `README.md`.

> Welcome to the {course name} course! 👋
>
> Before we start, we are going to download a small tool called `e0`. It is a Python script that manages your course: it fetches content, assigns you tasks through GitHub issues, and manages your progress.
>
> It will live in the `.exit0/` folder in your repo. That folder is for internal course use. You can safely ignore it throughout the course.
>
> You do not need to use `e0` directly. I will use it on your behalf.
>
> {a short, friendly closing line in the student's language}

Then run:

```bash
RELEASE=v1.3
curl -fsSL "https://raw.githubusercontent.com/exit0-io/e0/${RELEASE}/cli/bin/e0" -o .exit0/e0 \
  || curl -fsSL "https://github.com/exit0-io/e0/releases/latest/download/e0" -o .exit0/e0
chmod +x .exit0/e0
.exit0/e0 init
```

On Windows (PowerShell), run this instead, and from then on run every `e0` command as `python .exit0/e0 ...`:

```powershell
$RELEASE="v1.3"
curl.exe -fsSL "https://raw.githubusercontent.com/exit0-io/e0/$RELEASE/cli/bin/e0" -o .exit0/e0
if (-not $?) { curl.exe -fsSL "https://github.com/exit0-io/e0/releases/latest/download/e0" -o .exit0/e0 }
python .exit0/e0 init
```

`RELEASE` pins the version this skill was written for. When that download fails (for example, the tag is not published yet), the second `curl` takes the **latest release**. Never search for a version by hand.

`init` prints JSON. On `problem`, tell the student the `message` in plain words and help them fix it (usually the internet connection or a missing `.exit0/config.json`). Continue only after `init` succeeds.

After `init` succeeds, send this one note, then go back to the `learning` skill, "Every session", step 2:

> 💡 **Tip!** Did you know this course was designed to be driven completely by a small, cheap model like Haiku or GPT-mini? Switch to one now. Same learning, a fraction of the cost.

## Updating

Update only when the student asks, or when `e0 status` says the current version should be updated. Tell the student what you did and why.

1. Target version: the one `e0 status` gave, otherwise the latest release.
2. Run one of these:

```bash
# a specific release
RELEASE=<target version>
curl -fsSL "https://raw.githubusercontent.com/exit0-io/e0/${RELEASE}/cli/bin/e0" -o .exit0/e0 && chmod +x .exit0/e0

# or the latest release
curl -fsSL "https://github.com/exit0-io/e0/releases/latest/download/e0" -o .exit0/e0 && chmod +x .exit0/e0
```

3. Run `.exit0/e0 init`. It also refreshes `.exit0/skills/` to match the new version.
4. Run `.exit0/e0 status` to confirm, then go back to the `learning` skill, "Every session", step 2.
