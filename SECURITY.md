# Security policy

## Scope

`reversibility/` is a pure-Python reference model. It imports nothing outside the
standard library, opens no files, makes no network calls, spawns no processes,
and keeps no state between calls. Every public entry point is a function over
enums and dataclasses. PyYAML appears only in the test suite, which reads one
file inside this repository using `yaml.safe_load`.

So the interesting failures here are not memory safety or injection. They are
grading defects: a case where the model returns a weaker oversight tier than the
definition in `scenario.md` requires. Anything that adopted this model as its
gate would then let an action run with less oversight than it should have. That
is the class of bug this policy is mainly about.

## Supported versions

| Version | Supported |
|---|---|
| v1.0.2 | yes |
| v1.0.1 | fixes land in the next tag |
| v1.0.0 | fixes land in the next tag |
| untagged `main` | no |

Conformance results are cited by tag (see RESULTS.md), so please name the tag you
tested when you report anything.

## Report privately

Report privately, before opening a public issue, if you find any of:

- A declared class and consequence tier that produce a *lower* oversight tier
  than `scenario.md` specifies.
- Fail-closed not firing: an undeclared, misspelled, or unrecognised class that
  resolves to anything other than the most restrictive class.
- A chain whose folded class is weaker than the worst declared class in it.
- Anything in the suite that lets a non-conforming implementation pass, since a
  passing run is what people cite.

## Report publicly

Ordinary issues belong in the tracker: documentation that contradicts the model,
a scenario you think is graded wrong in the *stricter* direction, missing cases,
packaging problems, test failures on your platform. None of those weaken a gate,
so there is nothing to protect by keeping them quiet.

## How to report

Use private vulnerability reporting on this repository, under the Security and
quality tab, "Report a vulnerability". If that is not available to you, email
mayur.agnihotri0021@gmail.com with `aisvs-c9-conformance` in the subject.

Useful in a report: the tag you tested, the declared class and consequence tier,
the oversight tier you got, the tier you expected, and the part of `scenario.md`
you are reading it against. A failing test case is ideal but not required.

## What to expect

This repository is maintained by one person alongside other work, so replies come
in days rather than hours. You will get an acknowledgement saying whether the
report is accepted, and if it is, the fix ships as a tagged release with the
divergence written up, because a suite that people cite cannot change silently.

If we disagree about whether a grading is a defect, the disagreement gets
recorded rather than closed. v1.0.1 exists because an independent conformance run
diverged from the reference, and the divergence turned out to be `scenario.md`
contradicting `model.py` rather than an error by the person running it.

## Credit

Reporters are named in the release notes and in RESULTS.md unless they ask not to
be.
