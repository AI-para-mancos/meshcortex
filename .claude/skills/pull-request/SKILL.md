---
name: pull-request
description: This skill should be used when the user asks to "open a PR", "create a pull request",
  "create a PR for this branch", or whenever Claude is about to run `gh pr create` in this
  repository. Enforces this project's PR title/body format, template, and confirmation workflow.
version: 0.1.0
---

# Pull requests for meshcortex

Open pull requests in this repository with a consistent title, body, and metadata, using GitHub's
own template so the structure holds regardless of which teammate's Claude Code session created it.

## Before creating

1. Confirm the branch is pushed. Pushing is an outward-facing action — only run
   `git push -u origin <branch>` after the user explicitly confirms it, same as any other push.
2. Read `git log <base>..HEAD` and `git diff <base>...HEAD` to see every commit that will be
   included, not just the latest one.
3. Find which issue this PR resolves, if any, so `## Linked issue` can be filled in accurately —
   don't guess a number.

## Title

A natural, descriptive sentence of what changed — less than 100 characters and no conventional
commits-style `type(scope):` prefix. Never let it default to the branch name auto-title-cased by
GitHub — write it by hand.

## Body

Follow `.github/PULL_REQUEST_TEMPLATE.md`: a `## Summary` with 1-3 bullet points and a
`## Test plan` checklist. Write the Summary as natural sentences/paragraphs — no manual
line-wrapping, even in a temp `.md` file staged for `--body-file`: this overrides the global
100-character prose-wrap preference, since GitHub renders a paragraph's internal line breaks as
nothing (soft-wrapped) and hard-wrapping only makes the raw source look broken up for no visual
benefit. Never restate the diff verbatim, and never mention AI authorship.

The Test plan should only list checks that add signal beyond what CI already guarantees — lint,
format, and tests already run automatically on every PR and gate the merge, so repeating them as
manual checkboxes is redundant noise, not a real verification step. Only include what a human (or
this session) actually has to go and check by hand: a manual scenario, a measurement, a real-world
run.

Only add `## Linked issue` with `Closes #<number>` when this PR genuinely resolves an issue you
can identify — don't add the section, even empty, when no issue applies or none can be deduced.

## Metadata

Only set metadata if `gh` is available and the user has confirmed it.

- Assign the PR to its author (the user driving this session) by default; only assign someone
  else when they should clearly own the review instead.
- Labels are the user's call, not something to enforce or strip. When creating a PR, suggest one
  from `gh label list` if something genuinely fits — don't force a default, and never remove a
  label already present on an existing PR just because this skill didn't add it.
- Don't attach a milestone or an Issue Type to the PR, and don't add it to the "meshcortex
  roadmap" Project. That metadata belongs on the issue the PR closes, not the PR itself — a
  `Closes #<number>` link already makes it one click away, and duplicating it here is exactly the
  kind of drift-prone bookkeeping this repo's issue/PR metadata was cleaned up to avoid.
- `.github/CODEOWNERS` already routes review requests; no need to manually pick reviewers.

## Confirmation

Never run `gh pr create` without first showing the drafted title, body, and chosen metadata, and
waiting for confirmation — the same rule as committing. Creating a PR is outward-facing and
cannot be quietly undone.

## Additional resources

- `.claude/skills/conventional-commits/SKILL.md` — companion skill for the commits that make up
  this PR.
- `.github/PULL_REQUEST_TEMPLATE.md` — the body template this skill fills in.
