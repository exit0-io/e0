# Setup and Update

This is a reference for the `learning` skill. You come here from its "Start of every session" section, and you go back there when you finish.

## First-time setup

If the file `.exit0/e0` does not exist, the student is taking their first step in the course. Greet them and explain what is about to run. Use this template. The course name is the title of the repo's `README.md`.

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

On Windows (PowerShell), run this instead, and from now on run every `e0` command as `python .exit0/e0 ...`:

```powershell
$RELEASE="v1.3"
curl.exe -fsSL "https://raw.githubusercontent.com/exit0-io/e0/$RELEASE/cli/bin/e0" -o .exit0/e0
if (-not $?) { curl.exe -fsSL "https://github.com/exit0-io/e0/releases/latest/download/e0" -o .exit0/e0 }
python .exit0/e0 init
```

About the release: `RELEASE` pins the version of `e0` this skill was written for. If that release cannot be downloaded (for example, the tag does not exist yet), or if no release is given, the second `curl` takes the **latest release** automatically. Never stop to look for a version by hand.

`init` prints JSON. If it has a `problem` key, tell the student the `message` in plain words and help them fix it (usually it is the internet connection or a missing `.exit0/config.json`). Do not continue until `init` succeeds.

After `init` succeeds you MUST send these two short notes, then go back to the `learning` skill, "Start of every session", step 2. Keep them this short. They are read in the chat panel, and the emojis are there to catch the eye.

> 🔓 **One small setting:** please allow `.exit0/e0` to run without asking you each time. It runs the whole course and sends nothing anywhere.
>
> 💡 **Tip!** Did you know this course was designed to be driven completely by a small, cheap model like Haiku or GPT-mini? Switch to one now. Same learning, a fraction of the cost.

## Updating

> Never update silently. Tell the student what you did and why.

When the student asks to update `e0`, or when `e0 status` reports that the current version should be updated:

1. Find the target version. If `e0 status` gave you one, use it. Otherwise use the latest release.
2. Run one of these:

```bash
# a specific release
RELEASE=<target version>
curl -fsSL "https://raw.githubusercontent.com/exit0-io/e0/${RELEASE}/cli/bin/e0" -o .exit0/e0 && chmod +x .exit0/e0

# or simply the latest release
curl -fsSL "https://github.com/exit0-io/e0/releases/latest/download/e0" -o .exit0/e0 && chmod +x .exit0/e0
```

3. Run `.exit0/e0 init`. It also refreshes the skills in `.exit0/skills/` to match the new version.
4. Run `.exit0/e0 status` to confirm it works, then go back to the `learning` skill, "Start of every session", step 2.

Do not update unless the student asked, or the `e0 status` output says the current version should be updated.
