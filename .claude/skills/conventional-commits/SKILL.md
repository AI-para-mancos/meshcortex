---
name: conventional-commits
description: This skill should be used when the user asks to "commit this", "create a commit",
  "commit these changes", or whenever Claude is about to stage and commit changes in this
  repository. Enforces this project's Conventional Commits format, message rules, and confirmation
  workflow.
version: 0.1.0
---

# Conventional Commits for meshcortex

Draft and create git commits that follow this repository's Conventional Commits standard, so every
commit reads consistently regardless of which teammate's Claude Code session authored it.

## Format

Use `<type>(<scope>): <subject>` in imperative mood ("add", not "added"/"adds"), no trailing period,
lowercase after the prefix. Keep the whole title line — including the prefix — to 50 characters
or fewer; shorten the scope or subject rather than going over.

Common types: `feat`, `fix`, `refactor`, `perf`, `style`, `test`, `docs`, `build`, `ci`, `chore`.

Treat a commit as one atomic change. Split it into more than one commit if the subject needs
"and"/"also" to describe it.

## Body

Add a body only when the title and diff alone don't convey the why (rationale, trade-offs, context).
Never restate what's visible in the diff, test-pass status, time spent, or AI attribution. Omit
the body when in doubt. Wrap body lines at 100 characters or fewer.

## Rules specific to this repo

- Never add a `Co-Authored-By` line for Claude.
- When a commit relates to a known GitHub issue, add a `Ref: <issue-number>` footer line
  (e.g. `Ref: 123`) — the one exception to this repo's no-issue-reference rule, which only covers
  code, comments, and docs, not commit footers. Only add it when the issue is identifiable
  (e.g. from the branch name or something the user stated); never guess a number.
- Write every commit message in English, regardless of the conversation's language.

## Workflow

1. Run `git status`, `git diff` (staged and unstaged), and `git log` to see the change and match
   the repo's existing message style.
2. Stage only the files that belong to this atomic change by name — never `git add -A` or
   `git add .`.
3. Draft the commit message following the format above.
4. Show the staged diff and the drafted message, then wait for explicit confirmation.
   Never run `git commit` without it.
5. If a pre-commit hook fails (ruff lint/format, see `CONTRIBUTING.md`), fix the underlying issue,
   re-stage, and create a **new** commit — never `--no-verify`, `--amend` on a hook failure,
   or skip hooks.
6. Never push. Pushing is the user's action only.

## Additional resources

- `.claude/skills/pull-request/SKILL.md` — companion skill for opening the pull request once
  commits are ready.
- `CONTRIBUTING.md` — local pre-commit/ruff setup that runs on every commit.
