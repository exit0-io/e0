# Using the knowledge base

Use when the student asks about a concept, or asks to read a tutorial.

## What the knowledge base is

The course's own explanations of the concepts its tasks rely on. Every task lists its
related topics. `.exit0/course/knowledgebase/index.json` holds the title, topics, and a
one-line summary of each — read it, it is small and always on disk.

## When they ask about a covered topic

Say the course covers it, and point them at the tutorial. The course's explanation is the
one later tasks use, so giving them a different one will make those tasks harder to
understand.

You may still answer their immediate question. Point at the tutorial as well, not instead.

## When they ask to read something

Run `e0 read <topic>`. It lands personalized on disk. Tell them the path.

## Never

- Never assess what the student knows. Do not quiz them to find out, and do not infer it
  from how they are doing. If they want a tutorial they will ask.
- Never tell them to go read something instead of answering. Answer, then point.
