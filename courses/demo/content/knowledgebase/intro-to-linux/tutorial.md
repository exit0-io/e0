# Intro to Linux

The shell is how you talk to the operating system.

## Pipes

The `|` character sends the output of one command into the input of the next.

```bash
cat access.log | grep ERROR | wc -l
```
