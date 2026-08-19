# Say hello

## Related Topics

- Intro to Linux

## Setup

<!-- e0:variant id="run-tests" -->
<!-- when: os=linux -->
```bash
python3 -m pytest .exit0/tasks/t010/checks -v
```
<!-- when: os=macos -->
```bash
python3 -m pytest .exit0/tasks/t010/checks -v
```
<!-- when: os=windows -->
```powershell
py -m pytest .exit0\tasks\t010\checks -v
```
<!-- /e0:variant -->

<!-- e0:retone based-on="the student's Python experience" -->
<!-- /e0:retone -->

## Task

Create `greeting.py` in the repository root with a function `greet(name)` that returns
`Hello, <name>!`.

Build it using the **standard library** only.
